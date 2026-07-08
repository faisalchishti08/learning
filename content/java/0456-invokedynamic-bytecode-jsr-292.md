---
card: java
gi: 456
slug: invokedynamic-bytecode-jsr-292
title: invokedynamic bytecode (JSR 292)
---

## 1. What it is

`invokedynamic`, added in Java 7 as JSR 292, is a JVM bytecode instruction — one of the handful of "method invocation" instructions the JVM understands, alongside the older `invokevirtual`, `invokestatic`, `invokespecial`, and `invokeinterface`. Unlike those older instructions, which the JVM resolves to a specific method at class-loading time based on a fixed type, `invokedynamic` defers the decision of *what to actually call* to a "bootstrap method," resolved lazily — and potentially differently for different call sites, or changeably over the life of the program.

## 2. Why & when

`invokedynamic` was originally added to support **dynamically-typed languages** running on the JVM (JRuby, Jython, Groovy, and similar) — languages where a method call's actual target often can't be determined until runtime, since the type of the receiver might not be known or fixed in the way a statically-typed Java method call is. Without `invokedynamic`, implementing such a language on the JVM meant generating clunky, indirect bytecode (reflection-based dispatch, or hand-rolled lookup tables) to emulate dynamic dispatch — `invokedynamic` gave language implementers a proper, efficient, JVM-native primitive for this instead.

For years after Java 7, ordinary Java code itself never generated `invokedynamic` at all — it was purely for other JVM languages' benefit. That changed starting with **Java 8's lambda expressions**: `javac` began compiling lambdas using `invokedynamic` (rather than generating a separate synthetic class per lambda, as anonymous classes require), deferring the actual lambda-implementing-class creation to runtime. Java 9 extended this further, using `invokedynamic` (via `StringConcatFactory`) to implement `+`-based string concatenation more efficiently than the `StringBuilder`-chain bytecode javac used to generate. You don't call `invokedynamic` from Java source code directly — it only ever shows up as a detail of *how the compiler chose to implement* certain language features.

## 3. Core concept

```java
Runnable task = () -> System.out.println("hello"); // a lambda expression

// javac compiles this using invokedynamic -- the actual class implementing Runnable
// for this lambda is generated LAZILY, at runtime, the first time this code path executes,
// rather than existing as a separate .class file the compiler generated up front.
```

Because `invokedynamic` is a bytecode-level detail, it's not something you write or call directly in Java source — you can only observe its presence by disassembling compiled bytecode with `javap -c`, which is exactly what the runnable examples below do programmatically.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An anonymous class compiles into a completely separate class file with a fixed method call resolved at compile time; a lambda compiles into an invokedynamic call site whose actual implementation is linked lazily at runtime">
  <rect x="8" y="8" width="624" height="154" rx="8" fill="#0d1117"/>
  <text x="20" y="26" fill="#f85149" font-size="11" font-family="sans-serif">Anonymous class: a SEPARATE .class file, resolved at compile time</text>
  <rect x="30" y="38" width="560" height="26" rx="4" fill="#1c2430" stroke="#f85149"/><text x="310" y="56" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">invokespecial / invokevirtual -- fixed target, known at compile time</text>

  <text x="20" y="100" fill="#6db33f" font-size="11" font-family="sans-serif">Lambda: ONE invokedynamic call site, target linked lazily</text>
  <rect x="30" y="112" width="560" height="26" rx="4" fill="#1c2430" stroke="#6db33f"/><text x="310" y="130" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">invokedynamic -- bootstrap method decides the real target at runtime</text>
</svg>

Anonymous classes are a compile-time-fixed mechanism; lambdas defer their actual implementation to a lazily-linked runtime call site.

## 5. Runnable example

Scenario: inspecting real compiled bytecode to observe `invokedynamic` directly — the same investigation, evolved from confirming a lambda's bytecode contains it, through comparing a lambda against an equivalent anonymous class side by side, to observing a second, entirely different Java feature (`+`-based string concatenation) that also relies on `invokedynamic` under the hood.

### Level 1 — Basic

```java
import java.nio.file.*;
import java.io.*;

public class InvokeDynamicBasic {
    public static void main(String[] args) throws Exception {
        Path tempDir = Files.createTempDirectory("invokedynamic-demo");
        Path source = tempDir.resolve("LambdaExample.java");
        Files.writeString(source, """
            public class LambdaExample {
                public static void main(String[] args) {
                    Runnable task = () -> System.out.println("hello");
                    task.run();
                }
            }
            """);

        String javaHome = System.getProperty("java.home");
        String javacPath = javaHome + File.separator + "bin" + File.separator + "javac";
        String javapPath = javaHome + File.separator + "bin" + File.separator + "javap";

        // Compile the lambda example using the real javac executable
        new ProcessBuilder(javacPath, source.toString()).inheritIO().start().waitFor();

        // Disassemble it with javap and capture the output
        Process javap = new ProcessBuilder(javapPath, "-c", tempDir.resolve("LambdaExample.class").toString())
            .redirectErrorStream(true).start();
        String bytecode = new String(javap.getInputStream().readAllBytes());
        javap.waitFor();

        long invokedynamicCount = bytecode.lines().filter(line -> line.contains("invokedynamic")).count();
        System.out.println("invokedynamic instructions found in the lambda's bytecode: " + invokedynamicCount);
    }
}
```

**How to run:** `java InvokeDynamicBasic.java`

This writes a small lambda-using source file to a temp directory, compiles it with the real `javac` executable (located via `System.getProperty("java.home")`), then disassembles the result with `javap -c` and counts occurrences of `"invokedynamic"` in the output — confirming, directly from real compiled bytecode, that the lambda expression genuinely compiles down to this instruction.

### Level 2 — Intermediate

```java
import java.nio.file.*;
import java.io.*;

public class InvokeDynamicCompare {
    static long countInvokedynamic(Path tempDir, String className, String source) throws Exception {
        Path sourceFile = tempDir.resolve(className + ".java");
        Files.writeString(sourceFile, source);

        String javaHome = System.getProperty("java.home");
        String javacPath = javaHome + File.separator + "bin" + File.separator + "javac";
        String javapPath = javaHome + File.separator + "bin" + File.separator + "javap";

        new ProcessBuilder(javacPath, sourceFile.toString()).inheritIO().start().waitFor();

        Process javap = new ProcessBuilder(javapPath, "-c", tempDir.resolve(className + ".class").toString())
            .redirectErrorStream(true).start();
        String bytecode = new String(javap.getInputStream().readAllBytes());
        javap.waitFor();

        return bytecode.lines().filter(line -> line.contains("invokedynamic")).count();
    }

    public static void main(String[] args) throws Exception {
        Path tempDir = Files.createTempDirectory("invokedynamic-compare");

        String anonymousSource = """
            public class AnonymousExample {
                public static void main(String[] args) {
                    Runnable task = new Runnable() {
                        public void run() { System.out.println("hello"); }
                    };
                    task.run();
                }
            }
            """;

        String lambdaSource = """
            public class LambdaExample2 {
                public static void main(String[] args) {
                    Runnable task = () -> System.out.println("hello");
                    task.run();
                }
            }
            """;

        long anonymousCount = countInvokedynamic(tempDir, "AnonymousExample", anonymousSource);
        long lambdaCount = countInvokedynamic(tempDir, "LambdaExample2", lambdaSource);

        System.out.println("Anonymous class version -- invokedynamic count: " + anonymousCount);
        System.out.println("Lambda version -- invokedynamic count: " + lambdaCount);
        System.out.println("Lambda uses invokedynamic, anonymous class does not: "
            + (lambdaCount > 0 && anonymousCount == 0));
    }
}
```

**How to run:** `java InvokeDynamicCompare.java`

Two functionally-equivalent `Runnable` implementations — one an anonymous class, one a lambda — are compiled and disassembled the same way. The anonymous class compiles to zero `invokedynamic` instructions (it becomes an ordinary, separate class resolved with conventional invocation instructions); the lambda compiles to exactly one — direct, empirical confirmation of the difference in how `javac` implements each construct.

### Level 3 — Advanced

```java
import java.nio.file.*;
import java.io.*;

public class InvokeDynamicStringConcat {
    static String disassemble(Path tempDir, String className, String source) throws Exception {
        Path sourceFile = tempDir.resolve(className + ".java");
        Files.writeString(sourceFile, source);

        String javaHome = System.getProperty("java.home");
        String javacPath = javaHome + File.separator + "bin" + File.separator + "javac";
        String javapPath = javaHome + File.separator + "bin" + File.separator + "javap";

        new ProcessBuilder(javacPath, sourceFile.toString()).inheritIO().start().waitFor();

        Process javap = new ProcessBuilder(javapPath, "-c", "-v", tempDir.resolve(className + ".class").toString())
            .redirectErrorStream(true).start();
        String output = new String(javap.getInputStream().readAllBytes());
        javap.waitFor();
        return output;
    }

    public static void main(String[] args) throws Exception {
        Path tempDir = Files.createTempDirectory("invokedynamic-concat");

        String concatSource = """
            public class ConcatExample {
                public static void main(String[] args) {
                    String name = "World";
                    String greeting = "Hello, " + name + "!"; // string concatenation with a variable
                    System.out.println(greeting);
                }
            }
            """;

        String bytecode = disassemble(tempDir, "ConcatExample", concatSource);
        long invokedynamicCount = bytecode.lines().filter(line -> line.contains("invokedynamic")).count();
        boolean usesStringConcatFactory = bytecode.contains("StringConcatFactory");

        System.out.println("String concatenation invokedynamic count: " + invokedynamicCount);
        System.out.println("Uses java.lang.invoke.StringConcatFactory: " + usesStringConcatFactory);
    }
}
```

**How to run:** `java InvokeDynamicStringConcat.java`

Ordinary `+`-based string concatenation involving a variable also compiles to `invokedynamic`, on modern JDKs — specifically bootstrapped via `java.lang.invoke.StringConcatFactory`, a Java 9 change from the older `StringBuilder`-chain bytecode that `javac` used to generate for the same source code. This demonstrates that `invokedynamic`'s usefulness extended well beyond its original dynamic-language motivation, becoming a general optimization mechanism `javac` itself now relies on for more than one language feature.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `concatSource` defines a small program that concatenates a string literal, a variable (`name`), and another string literal using `+`.

`disassemble(tempDir, "ConcatExample", concatSource)` writes this source to a temporary file, then invokes the real `javac` executable (located via `System.getProperty("java.home") + "/bin/javac"`) as an external process via `ProcessBuilder`, compiling it into a genuine `.class` file. It then invokes `javap -c -v` (verbose disassembly, including constant pool details) as a second external process against that compiled class, capturing its full text output.

Back in `main`, `bytecode.lines().filter(line -> line.contains("invokedynamic")).count()` counts how many lines of the disassembly mention `invokedynamic` — on a modern JDK, string concatenation like this compiles to `invokedynamic` call sites (the exact count can reflect how the concatenation is broken into call sites internally, but at least one is always present for a genuine variable-involving concatenation). `bytecode.contains("StringConcatFactory")` checks whether the disassembly's constant pool references `java.lang.invoke.StringConcatFactory` — the specific bootstrap method class responsible for resolving these call sites at runtime.

Both checks confirm that this everyday, unremarkable-looking Java code (`"Hello, " + name + "!"`) is, since Java 9, implemented under the hood using the very same `invokedynamic` mechanism JSR 292 introduced back in Java 7 — originally for entirely different languages' benefit, now repurposed by `javac` itself for two distinct, common Java language features (lambdas and string concatenation).

Expected output:
```
String concatenation invokedynamic count: 2
Uses java.lang.invoke.StringConcatFactory: true
```

## 7. Gotchas & takeaways

> The exact number of `invokedynamic` call sites a given piece of source code compiles to is an **implementation detail** of the specific `javac` version being used, not something guaranteed by the Java Language Specification. The counts shown in these examples (one for a simple lambda, two for a particular string concatenation) reflect this JDK's current compiler behavior — don't write production code that depends on a specific `invokedynamic` count, since a future `javac` release could legitimately compile the same source differently.

- `invokedynamic` is a JVM bytecode instruction that defers method-call resolution to a runtime "bootstrap method," rather than resolving a fixed target at compile/class-load time like the older invocation instructions.
- It was introduced in Java 7 (JSR 292) primarily to support dynamically-typed JVM languages (JRuby, Groovy, and similar) — for years, ordinary Java code itself never generated it.
- Since Java 8, `javac` compiles **lambda expressions** using `invokedynamic`, deferring the actual implementing class's creation to runtime, rather than generating a separate synthetic class per lambda the way anonymous classes require.
- Since Java 9, `javac` also compiles `+`-based **string concatenation** involving variables using `invokedynamic`, via `java.lang.invoke.StringConcatFactory`, replacing the older `StringBuilder`-chain bytecode pattern.
- You never write `invokedynamic` directly in Java source — it's purely an implementation detail of how the compiler chooses to realize certain language features, observable only by disassembling compiled bytecode with a tool like `javap -c`.
