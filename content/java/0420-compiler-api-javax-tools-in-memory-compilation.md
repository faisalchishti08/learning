---
card: java
gi: 420
slug: compiler-api-javax-tools-in-memory-compilation
title: Compiler API javax.tools (in-memory compilation)
---

## 1. What it is

`javax.tools`, added in Java 6, exposes the Java compiler itself as an API you can call from your own code — `ToolProvider.getSystemJavaCompiler()` returns a `JavaCompiler` instance (the same compiler behind the `javac` command) that you can invoke programmatically via `run()` (simple, file-based) or `getTask()` (fully customizable, including compiling from and to **memory** rather than disk, by supplying your own `JavaFileObject` and `JavaFileManager` implementations).

## 2. Why & when

Before this API, compiling Java source code from within a running Java program meant shelling out to an external `javac` process — spawning a subprocess, writing source to temporary files on disk, capturing stdout/stderr, and reading back compiled `.class` files, all fragile and slow. `javax.tools` lets you compile source **in the same JVM process**, optionally never touching disk at all, and get structured, typed `Diagnostic` objects for any errors instead of parsing text output.

You reach for this whenever an application needs to compile Java code it doesn't have ahead of time — a plugin system that accepts user-submitted Java snippets, a REPL-like tool, dynamically generating and compiling boilerplate code, or (as the next tutorial covers) driving custom annotation processors programmatically. It's also the foundation many build tools and IDEs use for in-process compilation and live error-checking.

## 3. Core concept

```java
import javax.tools.*;

JavaCompiler compiler = ToolProvider.getSystemJavaCompiler(); // requires a JDK, not just a JRE

// Simplest form: compile a file on disk
int resultCode = compiler.run(null, null, null, "MyClass.java"); // 0 = success

// Full control: getTask() lets you supply custom file managers/objects for true in-memory compilation
JavaCompiler.CompilationTask task = compiler.getTask(
    null,            // Writer for extra output (null = System.err)
    fileManager,     // where source comes from / compiled classes go
    diagnostics,      // collects errors and warnings as structured objects
    null,            // compiler options
    null,            // classes for annotation processing
    compilationUnits // the source files (or in-memory equivalents) to compile
);
boolean success = task.call();
```

`ToolProvider.getSystemJavaCompiler()` returns `null` if run on a JRE without the compiler bundled (this API requires a full JDK) — always check for `null` before using it in production code.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="JavaCompiler.getTask combines source, a file manager, and a diagnostics collector; calling it produces compiled bytecode plus any errors, all without shelling out to an external process">
  <rect x="8" y="8" width="624" height="174" rx="8" fill="#0d1117"/>
  <rect x="30" y="30" width="150" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/><text x="105" y="55" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Source (in memory)</text>

  <rect x="245" y="60" width="150" height="60" rx="6" fill="#1c2430" stroke="#6db33f"/><text x="320" y="85" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">JavaCompiler</text><text x="320" y="103" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">getTask().call()</text>

  <rect x="460" y="30" width="150" height="40" rx="6" fill="#1c2430" stroke="#e6edf3"/><text x="535" y="55" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">.class bytes (in memory)</text>
  <rect x="460" y="120" width="150" height="40" rx="6" fill="#1c2430" stroke="#f85149"/><text x="535" y="145" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">Diagnostics (errors)</text>

  <line x1="180" y1="50" x2="240" y2="80" stroke="#8b949e" marker-end="url(#az1)"/>
  <line x1="395" y1="80" x2="455" y2="50" stroke="#8b949e" marker-end="url(#az1)"/>
  <line x1="395" y1="95" x2="455" y2="130" stroke="#8b949e" marker-end="url(#az1)"/>
  <defs><marker id="az1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Source goes in, either compiled bytecode or structured diagnostics come out — all inside the same process, with disk I/O entirely optional.

## 5. Runnable example

Scenario: a plugin system that compiles a small Java class supplied as a `String` at runtime and immediately runs a method on it — the same compile-and-run task, evolved from compiling to real files on disk, through fully in-memory compilation with no disk I/O at all, to a version that collects structured diagnostics and handles a compile error gracefully.

### Level 1 — Basic

```java
import javax.tools.*;
import java.io.*;
import java.net.*;
import java.nio.file.*;

public class InMemoryCompileBasic {
    public static void main(String[] args) throws Exception {
        String source =
            "public class Greeter {\n" +
            "    public String greet(String name) { return \"Hello, \" + name + \"!\"; }\n" +
            "}\n";

        Path tempDir = Files.createTempDirectory("compiler-demo");
        Path sourceFile = tempDir.resolve("Greeter.java");
        Files.writeString(sourceFile, source);

        JavaCompiler compiler = ToolProvider.getSystemJavaCompiler();
        int result = compiler.run(null, null, null, sourceFile.toString()); // writes Greeter.class to disk
        System.out.println("Compilation result (0 = success): " + result);

        URLClassLoader classLoader = new URLClassLoader(new URL[]{tempDir.toUri().toURL()});
        Class<?> greeterClass = Class.forName("Greeter", true, classLoader);
        Object greeter = greeterClass.getDeclaredConstructor().newInstance();
        String message = (String) greeterClass.getMethod("greet", String.class).invoke(greeter, "World");
        System.out.println(message);
    }
}
```

**How to run:** `java InMemoryCompileBasic.java`

`compiler.run(...)` is the simplest entry point — it works much like invoking `javac` directly, writing a real `Greeter.class` file to a temporary directory, which is then loaded via `URLClassLoader` and invoked through reflection. This demonstrates the basic capability but still touches disk for both the source and the compiled output.

### Level 2 — Intermediate

```java
import javax.tools.*;
import java.io.*;
import java.net.URI;
import java.util.*;

public class InMemoryCompileTrue {

    static class InMemorySource extends SimpleJavaFileObject {
        final String code;
        InMemorySource(String className, String code) {
            super(URI.create("string:///" + className.replace('.', '/') + Kind.SOURCE.extension), Kind.SOURCE);
            this.code = code;
        }
        @Override public CharSequence getCharContent(boolean ignoreEncodingErrors) { return code; }
    }

    static class InMemoryClassFile extends SimpleJavaFileObject {
        final ByteArrayOutputStream bytes = new ByteArrayOutputStream();
        InMemoryClassFile(String className) {
            super(URI.create("bytes:///" + className.replace('.', '/') + Kind.CLASS.extension), Kind.CLASS);
        }
        @Override public OutputStream openOutputStream() { return bytes; }
        byte[] getBytes() { return bytes.toByteArray(); }
    }

    static class InMemoryFileManager extends ForwardingJavaFileManager<StandardJavaFileManager> {
        final Map<String, InMemoryClassFile> classFiles = new HashMap<>();
        InMemoryFileManager(StandardJavaFileManager fileManager) { super(fileManager); }

        @Override
        public JavaFileObject getJavaFileForOutput(Location location, String className,
                                                    JavaFileObject.Kind kind, FileObject sibling) {
            InMemoryClassFile classFile = new InMemoryClassFile(className); // captures bytecode instead of writing a file
            classFiles.put(className, classFile);
            return classFile;
        }
    }

    static class InMemoryClassLoader extends ClassLoader {
        final Map<String, InMemoryClassFile> classFiles;
        InMemoryClassLoader(Map<String, InMemoryClassFile> classFiles) { this.classFiles = classFiles; }
        @Override
        protected Class<?> findClass(String name) throws ClassNotFoundException {
            InMemoryClassFile file = classFiles.get(name);
            if (file == null) throw new ClassNotFoundException(name);
            byte[] bytes = file.getBytes();
            return defineClass(name, bytes, 0, bytes.length); // defines the class straight from the byte array
        }
    }

    public static void main(String[] args) throws Exception {
        String source =
            "public class Greeter {\n" +
            "    public String greet(String name) { return \"Hello, \" + name + \"!\"; }\n" +
            "}\n";

        JavaCompiler compiler = ToolProvider.getSystemJavaCompiler();
        InMemoryFileManager fileManager = new InMemoryFileManager(
            compiler.getStandardFileManager(null, null, null));

        JavaCompiler.CompilationTask task = compiler.getTask(
            null, fileManager, null, null, null,
            List.of(new InMemorySource("Greeter", source)));

        boolean success = task.call();
        System.out.println("Compiled entirely in memory, success: " + success);

        InMemoryClassLoader classLoader = new InMemoryClassLoader(fileManager.classFiles);
        Class<?> greeterClass = Class.forName("Greeter", true, classLoader);
        Object greeter = greeterClass.getDeclaredConstructor().newInstance();
        String message = (String) greeterClass.getMethod("greet", String.class).invoke(greeter, "World");
        System.out.println(message);
    }
}
```

**How to run:** `java InMemoryCompileTrue.java`

Neither the source nor the compiled `.class` ever touches disk: `InMemorySource` supplies source text directly from a `String`, `InMemoryFileManager.getJavaFileForOutput` intercepts the compiler's request to write output and captures the bytecode into a `ByteArrayOutputStream` instead, and `InMemoryClassLoader.findClass` defines the class directly from those captured bytes.

### Level 3 — Advanced

```java
import javax.tools.*;
import java.io.*;
import java.net.URI;
import java.util.*;

public class InMemoryCompileDiagnostics {

    static class InMemorySource extends SimpleJavaFileObject {
        final String code;
        InMemorySource(String className, String code) {
            super(URI.create("string:///" + className.replace('.', '/') + Kind.SOURCE.extension), Kind.SOURCE);
            this.code = code;
        }
        @Override public CharSequence getCharContent(boolean ignoreEncodingErrors) { return code; }
    }

    static class InMemoryClassFile extends SimpleJavaFileObject {
        final ByteArrayOutputStream bytes = new ByteArrayOutputStream();
        InMemoryClassFile(String className) {
            super(URI.create("bytes:///" + className.replace('.', '/') + Kind.CLASS.extension), Kind.CLASS);
        }
        @Override public OutputStream openOutputStream() { return bytes; }
        byte[] getBytes() { return bytes.toByteArray(); }
    }

    static class InMemoryFileManager extends ForwardingJavaFileManager<StandardJavaFileManager> {
        final Map<String, InMemoryClassFile> classFiles = new HashMap<>();
        InMemoryFileManager(StandardJavaFileManager fileManager) { super(fileManager); }
        @Override
        public JavaFileObject getJavaFileForOutput(Location location, String className,
                                                    JavaFileObject.Kind kind, FileObject sibling) {
            InMemoryClassFile classFile = new InMemoryClassFile(className);
            classFiles.put(className, classFile);
            return classFile;
        }
    }

    static class InMemoryClassLoader extends ClassLoader {
        final Map<String, InMemoryClassFile> classFiles;
        InMemoryClassLoader(Map<String, InMemoryClassFile> classFiles) { this.classFiles = classFiles; }
        @Override
        protected Class<?> findClass(String name) throws ClassNotFoundException {
            InMemoryClassFile file = classFiles.get(name);
            if (file == null) throw new ClassNotFoundException(name);
            byte[] bytes = file.getBytes();
            return defineClass(name, bytes, 0, bytes.length);
        }
    }

    static boolean compileAndMaybeRun(String className, String source) throws Exception {
        JavaCompiler compiler = ToolProvider.getSystemJavaCompiler();
        InMemoryFileManager fileManager = new InMemoryFileManager(
            compiler.getStandardFileManager(null, null, null));
        DiagnosticCollector<JavaFileObject> diagnostics = new DiagnosticCollector<>();

        JavaCompiler.CompilationTask task = compiler.getTask(
            null, fileManager, diagnostics, null, null,
            List.of(new InMemorySource(className, source)));

        boolean success = task.call();

        if (!success) {
            System.out.println("Compilation FAILED for " + className + ":");
            for (Diagnostic<? extends JavaFileObject> d : diagnostics.getDiagnostics()) {
                System.out.println("  Line " + d.getLineNumber() + ": " + d.getMessage(null));
            }
            return false;
        }

        InMemoryClassLoader classLoader = new InMemoryClassLoader(fileManager.classFiles);
        Class<?> clazz = Class.forName(className, true, classLoader);
        Object instance = clazz.getDeclaredConstructor().newInstance();
        String message = (String) clazz.getMethod("greet", String.class).invoke(instance, "World");
        System.out.println(className + " compiled and ran: " + message);
        return true;
    }

    public static void main(String[] args) throws Exception {
        String goodSource =
            "public class GoodGreeter {\n" +
            "    public String greet(String name) { return \"Hello, \" + name + \"!\"; }\n" +
            "}\n";

        String badSource =
            "public class BadGreeter {\n" +
            "    public String greet(String name) { return \"Hello, \" + name \n" + // missing closing statement
            "}\n";

        compileAndMaybeRun("GoodGreeter", goodSource);
        compileAndMaybeRun("BadGreeter", badSource);
        System.out.println("Program continues after handling the compile failure.");
    }
}
```

**How to run:** `java InMemoryCompileDiagnostics.java`

`DiagnosticCollector<JavaFileObject>` captures every compiler error/warning as a structured `Diagnostic` object — with a real line number and message — rather than raw text, letting the caller decide exactly how to report a submitted snippet's problems; a plugin system can safely reject `badSource` and continue running rather than crashing.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. Two source strings are defined: `goodSource` (valid Java) and `badSource` (deliberately missing a closing statement, an invalid snippet).

`compileAndMaybeRun("GoodGreeter", goodSource)` runs first. Inside, a fresh `JavaCompiler`, `InMemoryFileManager`, and `DiagnosticCollector` are created; `compiler.getTask(...)` builds a `CompilationTask` wrapping the in-memory source. `task.call()` actually invokes the compiler: since `goodSource` is syntactically valid Java, compilation succeeds, `success` is `true`, and the `!success` branch is skipped. The method proceeds to load the compiled bytes via `InMemoryClassLoader`, instantiate `GoodGreeter`, call its `greet("World")` method via reflection (which returns `"Hello, World!"`), and prints `"GoodGreeter compiled and ran: Hello, World!"`.

`compileAndMaybeRun("BadGreeter", badSource)` runs next. This time, `task.call()` returns `false` — the source is missing a closing quote/semicolon and brace structure, a genuine syntax error. The `if (!success)` branch executes: it iterates `diagnostics.getDiagnostics()`, printing each diagnostic's line number and message — the compiler reports something like a missing `';'` at the line where the statement was cut off, and a second diagnostic noting the file ended unexpectedly while still parsing. The method then `return`s `false` **without** attempting to load or invoke any class, since none was successfully compiled — there is no bytecode to load.

Back in `main`, execution continues normally after both calls (`BadGreeter`'s failure was handled entirely within `compileAndMaybeRun`, not thrown as an uncaught exception), printing the final confirmation line.

Expected output (the exact diagnostic wording can vary slightly by JDK version, but the shape — one success, one handled failure — is stable):
```
GoodGreeter compiled and ran: Hello, World!
Compilation FAILED for BadGreeter:
  Line 2: ';' expected
  Line 3: reached end of file while parsing
Program continues after handling the compile failure.
```

## 7. Gotchas & takeaways

> `ToolProvider.getSystemJavaCompiler()` returns **`null`** when running on a JRE that doesn't bundle the compiler (this has been less common since Java 9 merged the JDK/JRE distinction, but it's still possible in minimized or custom runtime images built with `jlink`). Always null-check the returned `JavaCompiler` before using it, especially in code that might run in a stripped-down deployment environment.

- `compiler.run(...)` is the simple, file-based entry point; `compiler.getTask(...)` gives full control, including custom `JavaFileObject`/`JavaFileManager` implementations for true in-memory compilation.
- A custom `JavaFileObject` (extending `SimpleJavaFileObject`) can supply source text from anywhere — a `String`, a database, a network call — not just a file on disk.
- A custom `ForwardingJavaFileManager` overriding `getJavaFileForOutput` can capture compiled bytecode into memory instead of writing `.class` files, which a custom `ClassLoader` can then `defineClass` directly from.
- `DiagnosticCollector<JavaFileObject>` gives structured access to every compiler error and warning (with line numbers and messages), far more useful for programmatic handling than parsing raw `javac` console output.
- This API is the foundation for dynamically compiling and running submitted code, and (as the next tutorial shows) for driving custom annotation processors programmatically rather than only through a build tool's `-processor` flag.
