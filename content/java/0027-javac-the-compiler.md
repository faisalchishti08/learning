---
card: java
gi: 27
slug: javac-the-compiler
title: javac — the compiler
---

## 1. What it is

**`javac`** is the Java compiler that ships with the JDK. It translates `.java` source files into `.class` files containing JVM bytecode. `javac` is a JDK-only tool — it is not present in JRE-only images or `jlink` runtime images that don't include `jdk.compiler`.

`javac` performs: lexical analysis → parsing → type checking / name resolution → bytecode generation. It is itself written in Java, modular as `jdk.compiler`, and exposes a full programmatic API via the `javax.tools.JavaCompiler` interface.

## 2. Why & when

You invoke `javac` directly when:
- Learning or debugging — `javac Hello.java && java Hello`
- Writing build tools, code generators, or annotation processors
- Checking what a specific `--release` produces
- Using `javac -verbose` or `-Xlint` to diagnose compilation issues

In production, `javac` is called by build tools (Maven, Gradle, Ant) — you rarely invoke it manually. But understanding its flags matters when:
- `--release N` produces a class file targeting an older JVM
- `-parameters` retains method parameter names (Spring MVC uses this)
- `-proc:only` runs only annotation processors without producing class files
- `--enable-preview` enables preview features

## 3. Core concept

Key `javac` flags:

```
javac [options] <source files>

Source/class path:
  -sourcepath <path>     where to find .java source files
  -classpath / -cp <path> where to find compiled .class files / JARs
  --module-path <path>   (Java 9+) where to find modules

Output:
  -d <dir>               output directory for .class files
  -s <dir>               output directory for generated sources (annotation processing)

Compatibility:
  --release N            compile to target JVM version N (also sets source compat)
  -source N / -target N  (older form; --release is preferred as it also gates APIs)

Diagnostics:
  -verbose               print each compilation step
  -Xlint                 enable all recommended warnings
  -Xlint:unchecked       warn on unchecked generics operations
  -Werror                treat warnings as errors

Annotation processing:
  -processor <class>     specify annotation processor classes
  -proc:only             run processors but don't compile to .class
  -proc:none             skip annotation processing

Extras:
  -parameters            store formal parameter names in .class (needed by Spring MVC)
  --enable-preview       allow preview language features (requires --release)
  -g                     include all debug info (line numbers, vars, source)
  -g:none                strip all debug info
```

`--release N` vs `-source N -target N`: `--release N` also uses the bootclasspath of JDK N, preventing use of APIs added after N. `-source/-target` only sets the language and class file version, but lets you accidentally call APIs not in N.

## 4. Diagram

<svg viewBox="0 0 680 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="javac compilation pipeline: .java source through parsing, type-check, bytecode generation to .class">
  <rect x="10" y="10" width="660" height="200" rx="8" fill="#0d1117"/>

  <!-- Pipeline boxes -->
  <rect x="20"  y="60" width="90" height="40" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="65"  y="82" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">.java</text>
  <text x="65"  y="95" fill="#8b949e" font-size="8"  text-anchor="middle" font-family="sans-serif">source</text>

  <line x1="110" y1="80" x2="140" y2="80" stroke="#8b949e" stroke-width="1.5" marker-end="url(#ja)"/>

  <rect x="140" y="60" width="90" height="40" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="185"  y="82" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Lex+Parse</text>
  <text x="185"  y="95" fill="#8b949e" font-size="8"  text-anchor="middle" font-family="sans-serif">AST</text>

  <line x1="230" y1="80" x2="260" y2="80" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#ja2)"/>

  <rect x="260" y="60" width="90" height="40" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="305" y="82" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Type Check</text>
  <text x="305" y="95" fill="#8b949e" font-size="8"  text-anchor="middle" font-family="sans-serif">annotate AST</text>

  <line x1="350" y1="80" x2="380" y2="80" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#ja2)"/>

  <rect x="380" y="60" width="90" height="40" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="425" y="82" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">Bytecode gen</text>
  <text x="425" y="95" fill="#8b949e" font-size="8"  text-anchor="middle" font-family="sans-serif">Code attr.</text>

  <line x1="470" y1="80" x2="500" y2="80" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ja3)"/>

  <rect x="500" y="60" width="90" height="40" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="545" y="82" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">.class</text>
  <text x="545" y="95" fill="#8b949e" font-size="8"  text-anchor="middle" font-family="sans-serif">bytecode</text>

  <!-- annotation proc loop -->
  <path d="M 185 100 Q 185 155 305 155 Q 380 155 380 100" fill="none" stroke="#f0883e" stroke-width="1.5" stroke-dasharray="4,3" marker-end="url(#ja4)"/>
  <text x="285" y="175" fill="#f0883e" font-size="8" text-anchor="middle" font-family="sans-serif">annotation processors (may generate new .java → loop)</text>

  <!-- flags -->
  <text x="65" y="135" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">--release N</text>
  <text x="65" y="148" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">-cp</text>
  <text x="545" y="135" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">-d outdir</text>
  <text x="545" y="148" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">-parameters</text>

  <defs>
    <marker id="ja"  markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6" fill="none" stroke="#8b949e" stroke-width="1.5"/></marker>
    <marker id="ja2" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6" fill="none" stroke="#79c0ff" stroke-width="1.5"/></marker>
    <marker id="ja3" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6" fill="none" stroke="#6db33f" stroke-width="1.5"/></marker>
    <marker id="ja4" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6" fill="none" stroke="#f0883e" stroke-width="1.5"/></marker>
  </defs>
</svg>

`javac` pipeline: source → lex+parse (AST) → type-check → bytecode generation → `.class`. Annotation processors may inject new sources and re-trigger the loop.

## 5. Runnable example

Scenario: compile Java source programmatically using the `javax.tools.JavaCompiler` API — the same API IDEs and build tools use.

### Level 1 — Basic

```java
// JavacBasic.java
import javax.tools.*;
import java.util.List;

public class JavacBasic {
    public static void main(String[] args) throws Exception {
        JavaCompiler compiler = ToolProvider.getSystemJavaCompiler();
        if (compiler == null) {
            System.err.println("No javac available — run this on a JDK, not a JRE");
            System.exit(1);
        }

        System.out.println("javac available: true");
        System.out.println("Compiler class : " + compiler.getClass().getName());

        // Compile this very file if it exists on disk
        // (source-launch mode compiles to temp dir, but the source is readable)
        StandardJavaFileManager fm = compiler.getStandardFileManager(null, null, null);

        // Get the source of a temp file we write first
        java.nio.file.Path src = java.nio.file.Files.createTempFile("Hello", ".java");
        java.nio.file.Files.writeString(src,
            "public class Hello { public static void main(String[] a) { System.out.println(\"compiled!\"); }}");

        Iterable<? extends JavaFileObject> units = fm.getJavaFileObjects(src.toFile());

        // Compile to temp dir
        java.nio.file.Path outDir = java.nio.file.Files.createTempDirectory("javac-out");
        List<String> opts = List.of("-d", outDir.toString());

        boolean ok = compiler.getTask(null, fm, null, opts, null, units).call();
        System.out.println("Compilation succeeded: " + ok);
        System.out.println("Output dir: " + outDir);
        System.out.println("Files: " + java.util.Arrays.toString(outDir.toFile().list()));

        java.nio.file.Files.delete(src);
    }
}
```

**How to run:** `java JavacBasic.java` (requires JDK, not JRE-only)

`ToolProvider.getSystemJavaCompiler()` returns `null` on a JRE. On a JDK it returns an `javax.tools.JavaCompiler` — the same compiler `javac` command uses internally.

### Level 2 — Intermediate

Same compiler API extended to capture and display diagnostic messages — the way IDEs collect error/warning information with source locations.

```java
// JavacDiagnostics.java
import javax.tools.*;
import java.util.*;
import java.io.StringWriter;
import java.nio.file.*;

public class JavacDiagnostics {
    public static void main(String[] args) throws Exception {
        JavaCompiler compiler = ToolProvider.getSystemJavaCompiler();
        if (compiler == null) { System.err.println("JDK required"); return; }

        // Source with intentional errors
        Path src = Files.createTempFile("Broken", ".java");
        Files.writeString(src,
            "public class Broken {\n" +
            "    public static void main(String[] args) {\n" +
            "        int x = \"not an int\";  // type error\n" +
            "        undeclaredMethod();     // undefined method\n" +
            "        System.out.println(x);\n" +
            "    }\n" +
            "}\n");

        DiagnosticCollector<JavaFileObject> collector = new DiagnosticCollector<>();
        StandardJavaFileManager fm = compiler.getStandardFileManager(collector, null, null);
        Iterable<? extends JavaFileObject> units = fm.getJavaFileObjects(src.toFile());
        Path outDir = Files.createTempDirectory("javac-diag");

        boolean ok = compiler.getTask(null, fm, collector, List.of("-d", outDir.toString()), null, units).call();

        System.out.println("Compilation result: " + (ok ? "SUCCESS" : "FAILED"));
        System.out.println("\nDiagnostics collected:");

        for (Diagnostic<? extends JavaFileObject> d : collector.getDiagnostics()) {
            System.out.printf("[%s] line %d: %s%n",
                d.getKind(),          // ERROR, WARNING, NOTE
                d.getLineNumber(),
                d.getMessage(null));  // null = default locale
        }

        System.out.println("\nDiagnostic breakdown:");
        Map<Diagnostic.Kind, Long> counts = new LinkedHashMap<>();
        for (var d : collector.getDiagnostics()) {
            counts.merge(d.getKind(), 1L, Long::sum);
        }
        counts.forEach((k, v) -> System.out.printf("  %-8s %d%n", k, v));

        Files.delete(src);
    }
}
```

**How to run:** `java JavacDiagnostics.java`

`DiagnosticCollector` captures structured errors with source location, kind (ERROR/WARNING/NOTE), and message. IDEs use exactly this API to show red underlines with error messages.

### Level 3 — Advanced

Same javac API grown to compile a class, load it with a new `URLClassLoader`, and invoke a method — the pattern used by hot-reload tools, scripting engines, and annotation processor testing frameworks.

```java
// JavacAndLoad.java
import javax.tools.*;
import java.lang.reflect.*;
import java.net.*;
import java.nio.file.*;
import java.util.*;

public class JavacAndLoad {
    public static void main(String[] args) throws Exception {
        JavaCompiler compiler = ToolProvider.getSystemJavaCompiler();
        if (compiler == null) { System.err.println("JDK required"); return; }

        // Step 1: define source dynamically
        String className = "DynamicGreeter";
        String source =
            "public class " + className + " {\n" +
            "    public String greet(String name) {\n" +
            "        return \"Hello from dynamically compiled class, \" + name + \"!\";\n" +
            "    }\n" +
            "    public int version() { return 1; }\n" +
            "}\n";

        System.out.println("=== Compile → Load → Invoke ===\n");
        System.out.println("[Source]");
        System.out.println(source);

        // Step 2: compile to temp dir
        Path outDir = Files.createTempDirectory("javac-load");
        Path srcFile = outDir.resolve(className + ".java");
        Files.writeString(srcFile, source);

        DiagnosticCollector<JavaFileObject> diag = new DiagnosticCollector<>();
        StandardJavaFileManager fm = compiler.getStandardFileManager(diag, null, null);
        Iterable<? extends JavaFileObject> units = fm.getJavaFileObjects(srcFile.toFile());

        boolean ok = compiler.getTask(null, fm, diag, List.of("-d", outDir.toString()), null, units).call();

        if (!ok) {
            System.out.println("[Compile FAILED]");
            diag.getDiagnostics().forEach(d -> System.out.println("  " + d.getMessage(null)));
            return;
        }
        System.out.println("[Compile OK → " + outDir + "]");

        // Step 3: load the class
        URLClassLoader loader = new URLClassLoader(
            new URL[]{ outDir.toUri().toURL() },
            Thread.currentThread().getContextClassLoader());

        Class<?> cls = loader.loadClass(className);
        System.out.println("[Loaded] " + cls.getName() + " from " + cls.getClassLoader());

        // Step 4: invoke methods via reflection
        Object instance = cls.getDeclaredConstructor().newInstance();

        Method greet   = cls.getMethod("greet", String.class);
        Method version = cls.getMethod("version");

        System.out.println("[Invoke] greet(\"World\") → " + greet.invoke(instance, "World"));
        System.out.println("[Invoke] version()      → " + version.invoke(instance));

        // Step 5: recompile with version=2 (hot-reload pattern)
        String source2 = source.replace("return 1;", "return 2;")
                               .replace("Hello from", "Hello v2 from");
        Files.writeString(srcFile, source2);
        compiler.getTask(null, fm, null, List.of("-d", outDir.toString()), null,
            fm.getJavaFileObjects(srcFile.toFile())).call();

        URLClassLoader loader2 = new URLClassLoader(new URL[]{ outDir.toUri().toURL() }, null);
        Class<?> cls2 = loader2.loadClass(className);
        Object inst2  = cls2.getDeclaredConstructor().newInstance();
        System.out.println("\n[Hot-reload] greet → " + cls2.getMethod("greet", String.class).invoke(inst2, "Reload"));
        System.out.println("[Hot-reload] version → " + cls2.getMethod("version").invoke(inst2));

        loader.close(); loader2.close();
        Files.walk(outDir).sorted(Comparator.reverseOrder()).forEach(p -> p.toFile().delete());
    }
}
```

**How to run:** `java JavacAndLoad.java`

Each `URLClassLoader` is independent — class identity is `ClassLoader × className`. This is why hot-reload tools create a new classloader for each recompile rather than reusing the old one.

## 6. Walkthrough

Execution in `JavacAndLoad.main`:

1. **Source string** — `className = "DynamicGreeter"`. The class name must match the filename (`DynamicGreeter.java`). `javac` enforces this — a mismatch causes a compile error.

2. **`compiler.getTask(...).call()`** — returns `true` if compilation succeeded. Arguments: writer (null = stderr), file manager, diagnostic collector, options list (`-d outDir`), annotation processor names (null = discover via classpath), compilation units.

3. **`URLClassLoader`** — loads `.class` files from a `URL[]`. `outDir.toUri().toURL()` converts the temp directory path to a file:// URL. The second arg is the parent classloader — `Thread.currentThread().getContextClassLoader()` delegates unknown classes to the app classloader.

4. **`cls.getDeclaredConstructor().newInstance()`** — creates an instance via reflection. `DeclaredConstructor` finds the no-arg constructor even if it's non-public.

5. **Hot-reload** — a new `URLClassLoader` with a new URL (same directory, same class name) loads the recompiled class as a *different* `Class<?>` object. `loader` and `loader2` hold independent definitions of `DynamicGreeter`. Servlet containers (Tomcat, Jetty) and dev tools (Spring DevTools) use this pattern to reload changed classes without restarting the JVM.

## 7. Gotchas & takeaways

> **`--release N` is always preferable to `-source N -target N`** because it also gates the standard library to the APIs that existed in JDK N. With `-target 11` alone, you can accidentally call `String.isBlank()` (Java 11) while targeting a Java 8 JVM — `--release 8` prevents this at compile time.

> **`-parameters` flag is required for Spring MVC to resolve `@PathVariable` and `@RequestParam` names from method parameters.** Without it, Spring falls back to annotation values (`@PathVariable("id")`) — missing that value causes startup errors. Maven's `spring-boot-starter-parent` sets this flag automatically.

- `javac` is `jdk.compiler` module — absent in JRE-only images.
- `javax.tools.JavaCompiler` (programmatic API) is the same compiler `javac` CLI uses.
- `DiagnosticCollector` captures structured errors with line/column — the IDE API.
- `URLClassLoader` + `javac` = dynamic compile-and-load (used by dev-reload, scripting, testing).
- `--release N` prevents accidental use of APIs newer than N; prefer it over `-source/-target`.
