---
card: java
gi: 50
slug: compilation-lifecycle-source-bytecode-execution
title: Compilation lifecycle (source → bytecode → execution)
---

## 1. What it is

The **Java compilation lifecycle** is the three-stage journey every Java program takes from source code to running process:

1. **Source (`.java`)** — human-readable code you write.
2. **Bytecode (`.class`)** — platform-neutral instructions produced by `javac`.
3. **Execution** — the JVM loads `.class` files, JIT-compiles hot methods to native machine code, and runs your program.

Unlike C/C++, Java compiles to platform-neutral bytecode (not machine code). The JVM on each OS interprets and JIT-compiles that bytecode to native instructions at runtime — this is how "write once, run anywhere" works.

## 2. Why & when

Understanding this lifecycle matters because:
- **Compilation errors vs. runtime errors**: `javac` catches type errors, missing methods, and syntax errors at compile time. Logic errors and `NullPointerException` appear at runtime.
- **Classpath issues**: the JVM searches `.class` files at runtime using the classpath; understanding the lifecycle helps debug `ClassNotFoundException`.
- **Build tools**: Maven, Gradle, and IDEs all automate this lifecycle — knowing the stages makes error messages interpretable.
- **Performance**: JIT compilation means the first few calls to a method are slow (interpreted); after enough calls the JVM compiles that method to native code and it runs fast.

## 3. Core concept

```bash
# Stage 1: SOURCE (.java)
# ─────────────────────────────────────────────────────
# Human-readable Java source code in UTF-8 text files
# Each public class must be in a file named <ClassName>.java

# Stage 2: COMPILE (javac)
# ─────────────────────────────────────────────────────
javac Hello.java                      # → Hello.class
javac -d out/ src/Hello.java          # → out/Hello.class
javac -cp lib/*.jar -d out/ src/**/*.java   # multi-file with dependencies

# The .class file contains:
#   - Magic number (0xCAFEBABE)
#   - Bytecode instructions (JVM instruction set)
#   - Constant pool (string literals, method refs)
#   - Metadata (class name, super, interfaces, fields, methods)

# Inspect bytecode:
javap -c Hello.class          # disassemble bytecode
javap -verbose Hello.class    # full constant pool + metadata

# Stage 3: EXECUTE (java)
# ─────────────────────────────────────────────────────
java Hello                             # load Hello.class from current dir
java -cp out/ Hello                    # load from out/
java -cp out/:lib/deps.jar Hello      # with dependencies

# JVM lifecycle at runtime:
# 1. ClassLoader reads .class bytes
# 2. Bytecode verifier checks integrity
# 3. Interpreter runs bytecode (slow path)
# 4. JIT compiler detects "hot" methods (≥10,000 invocations by default)
# 5. JIT compiles hot methods to native machine code (fast path)
# 6. Program runs

# Single-file shortcut (JDK 11+): skip the javac step
java Hello.java        # javac + java in one command (temp .class not visible)
```

## 4. Diagram

<svg viewBox="0 0 700 195" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Java lifecycle: source to bytecode via javac, then JVM loads bytecode and JIT-compiles to native code">
  <rect x="8" y="8" width="684" height="179" rx="8" fill="#0d1117"/>

  <!-- Stage 1: Source -->
  <rect x="20" y="30" width="130" height="130" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="85" y="50" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Hello.java</text>
  <text x="35" y="68"  fill="#6db33f" font-size="8" font-family="monospace">public class Hello {</text>
  <text x="35" y="81"  fill="#8b949e" font-size="8" font-family="monospace">  public static</text>
  <text x="35" y="94"  fill="#8b949e" font-size="8" font-family="monospace">  void main(</text>
  <text x="35" y="107" fill="#8b949e" font-size="8" font-family="monospace">    String[] a) {</text>
  <text x="35" y="120" fill="#e6edf3" font-size="8" font-family="monospace">    sout("Hi");</text>
  <text x="35" y="133" fill="#8b949e" font-size="8" font-family="monospace">  }</text>
  <text x="35" y="147" fill="#8b949e" font-size="8" font-family="monospace">}</text>

  <!-- javac arrow -->
  <rect x="163" y="82" width="70" height="30" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="198" y="100" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">javac</text>
  <line x1="150" y1="95" x2="161" y2="95" stroke="#6db33f" stroke-width="1.5" marker-end="url(#lc1)"/>
  <line x1="233" y1="95" x2="244" y2="95" stroke="#6db33f" stroke-width="1.5" marker-end="url(#lc1)"/>

  <!-- Stage 2: Bytecode -->
  <rect x="247" y="30" width="145" height="130" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="320" y="50" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Hello.class</text>
  <text x="262" y="67"  fill="#8b949e" font-size="8" font-family="monospace">CAFEBABE 0000003D</text>
  <text x="262" y="81"  fill="#8b949e" font-size="8" font-family="monospace">getstatic #7</text>
  <text x="262" y="95"  fill="#8b949e" font-size="8" font-family="monospace">ldc #13 "Hi"</text>
  <text x="262" y="109" fill="#8b949e" font-size="8" font-family="monospace">invokevirtual #19</text>
  <text x="262" y="123" fill="#8b949e" font-size="8" font-family="monospace">return</text>
  <text x="262" y="145" fill="#79c0ff" font-size="7" font-family="sans-serif">platform-neutral</text>

  <!-- java arrow -->
  <rect x="403" y="82" width="58" height="30" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="432" y="100" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">java</text>
  <line x1="392" y1="95" x2="401" y2="95" stroke="#6db33f" stroke-width="1.5" marker-end="url(#lc1)"/>
  <line x1="461" y1="95" x2="472" y2="95" stroke="#6db33f" stroke-width="1.5" marker-end="url(#lc1)"/>

  <!-- Stage 3: JVM execution -->
  <rect x="475" y="30" width="205" height="130" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="578" y="50" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">JVM (runtime)</text>
  <text x="490" y="67"  fill="#8b949e" font-size="8" font-family="sans-serif">1. ClassLoader reads .class</text>
  <text x="490" y="81"  fill="#8b949e" font-size="8" font-family="sans-serif">2. Bytecode verifier checks</text>
  <text x="490" y="95"  fill="#8b949e" font-size="8" font-family="sans-serif">3. Interpreter runs bytecode</text>
  <text x="490" y="109" fill="#6db33f" font-size="8" font-family="sans-serif">4. JIT compiles hot methods</text>
  <text x="490" y="123" fill="#6db33f" font-size="8" font-family="sans-serif">5. Native code executes</text>
  <text x="490" y="148" fill="#e6edf3" font-size="8" font-family="monospace">Output: Hi</text>

  <defs>
    <marker id="lc1" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6" fill="none" stroke="#6db33f" stroke-width="1.5"/></marker>
  </defs>
</svg>

`javac` compiles platform-neutral bytecode; the JVM loads it, verifies it, and JIT-compiles hot paths to native code at runtime. The `.class` file is the same on all platforms — only the JVM is platform-specific.

## 5. Runnable example

Scenario: a string-transformation pipeline that we'll inspect at each stage of the compilation lifecycle — looking at the source, disassembling the bytecode, and observing JIT behaviour at runtime.

### Level 1 — Basic

```java
// LifecycleBasic.java — show the compilation lifecycle in one file
import java.nio.file.*;

public class LifecycleBasic {

    // A simple method we'll disassemble to see bytecode
    public static String transform(String input) {
        return input.trim().toUpperCase().replace(" ", "_");
    }

    public static void main(String[] args) throws Exception {
        System.out.println("=== Compilation lifecycle demo ===\n");

        // --- Stage 1: Source (we ARE the source right now) ---
        System.out.println("Stage 1: Source (.java)");
        System.out.println("  This file: LifecycleBasic.java");
        System.out.println("  java.version: " + System.getProperty("java.version"));

        // --- Stage 2: Bytecode ---
        // Find the .class file that the JVM loaded for this class
        String className = LifecycleBasic.class.getName().replace('.', '/') + ".class";
        System.out.println("\nStage 2: Bytecode (.class)");

        // Locate the class file
        var classUrl = LifecycleBasic.class.getResource("/" + className);
        if (classUrl != null) {
            Path classFile = Path.of(classUrl.toURI());
            byte[] bytes = Files.readAllBytes(classFile);
            System.out.printf("  Class file: %s%n", classFile.getFileName());
            System.out.printf("  Size: %d bytes%n", bytes.length);
            System.out.printf("  Magic: 0x%02X%02X%02X%02X (should be CAFEBABE)%n",
                bytes[0], bytes[1], bytes[2], bytes[3]);
            int majorVersion = ((bytes[6] & 0xFF) << 8) | (bytes[7] & 0xFF);
            System.out.printf("  Class file major version: %d (JDK %d)%n",
                majorVersion, majorVersion - 44);
        } else {
            System.out.println("  (class file location not accessible in this run mode)");
        }

        // --- Stage 3: Execution ---
        System.out.println("\nStage 3: Execution (JVM)");
        System.out.println("  JVM: " + System.getProperty("java.vm.name"));
        System.out.println("  Running method: transform()");

        String result = transform("  hello world  ");
        System.out.println("  transform('  hello world  ') → \"" + result + "\"");

        System.out.println("\n[ Disassemble bytecode ]");
        System.out.println("  javap -c LifecycleBasic.class");
        System.out.println("  (after compiling: javac LifecycleBasic.java)");
    }
}
```

**How to run:** `java LifecycleBasic.java`

The magic number `0xCAFEBABE` identifies every Java `.class` file. The class file major version encodes which JDK compiled it: major version 61 = JDK 17, 65 = JDK 21. `javap -c` disassembles bytecode — run it to see the actual instructions for `transform()`.

### Level 2 — Intermediate

Same pipeline scenario extended: compile a helper class at runtime using `javax.tools.JavaCompiler`, load it with a URLClassLoader, call the method — demonstrating all three lifecycle stages programmatically in one run.

```java
// LifecycleRuntime.java — compile + load + run a class at runtime
import javax.tools.*;
import java.io.*;
import java.lang.reflect.*;
import java.net.*;
import java.nio.file.*;

public class LifecycleRuntime {

    // The source we'll compile at runtime
    static final String TRANSFORMER_SOURCE =
        "public class RuntimeTransformer {\n" +
        "    public static String transform(String input) {\n" +
        "        return input.trim().toUpperCase().replace(\" \", \"_\");\n" +
        "    }\n" +
        "}\n";

    public static void main(String[] args) throws Exception {
        System.out.println("=== Runtime compilation lifecycle ===\n");

        JavaCompiler compiler = ToolProvider.getSystemJavaCompiler();
        if (compiler == null) { System.err.println("No JavaCompiler — JDK required"); return; }

        Path work = Files.createTempDirectory("lifecycle-demo");
        Path src  = work.resolve("RuntimeTransformer.java");
        Path cls  = work.resolve("RuntimeTransformer.class");

        // Stage 1: write source
        Files.writeString(src, TRANSFORMER_SOURCE);
        System.out.println("Stage 1: Source written to " + src.getFileName());

        // Stage 2: compile (javac programmatically)
        int rc = compiler.run(null, null, null, src.toString());
        if (rc != 0) { System.err.println("Compilation failed"); return; }
        long classSize = Files.size(cls);
        System.out.printf("Stage 2: Compiled → %s (%d bytes)%n",
            cls.getFileName(), classSize);

        // Read magic and version from .class
        byte[] header = Files.readAllBytes(cls);
        System.out.printf("  Magic: 0x%02X%02X%02X%02X | Major version: %d%n",
            header[0], header[1], header[2], header[3],
            ((header[6] & 0xFF) << 8) | (header[7] & 0xFF));

        // Stage 3: load and execute
        try (URLClassLoader loader = new URLClassLoader(new URL[]{work.toUri().toURL()})) {
            Class<?> clazz  = loader.loadClass("RuntimeTransformer");
            Method method   = clazz.getMethod("transform", String.class);

            System.out.println("\nStage 3: Loaded and executed via reflection");
            String[] inputs = {"  hello world  ", "java programming", "  CLEAN  ME  "};
            for (String input : inputs) {
                String result = (String) method.invoke(null, input);
                System.out.printf("  transform(\"%s\") → \"%s\"%n", input.trim(), result);
            }
        }

        // Show bytecode structure
        System.out.println("\n[ Bytecode instructions for transform() ]");
        System.out.println("  0: aload_0          // push arg 'input'");
        System.out.println("  1: invokevirtual #2 // String.trim()");
        System.out.println("  4: invokevirtual #3 // String.toUpperCase()");
        System.out.println("  7: ldc #4           // push ' '");
        System.out.println("  9: ldc #5           // push '_'");
        System.out.println(" 11: invokevirtual #6 // String.replace()");
        System.out.println(" 14: areturn          // return String");

        Files.walk(work).sorted(java.util.Comparator.reverseOrder()).forEach(f -> f.toFile().delete());
        System.out.println("\nCleaned up.");
    }
}
```

**How to run:** `java LifecycleRuntime.java`

`ToolProvider.getSystemJavaCompiler()` gives you programmatic access to `javac`. This is how IDEs, build tools, and code-generation frameworks compile code at runtime. `URLClassLoader` loads the compiled `.class` from a directory — demonstrating the ClassLoader stage of execution.

### Level 3 — Advanced

Same pipeline extended to measure JIT compilation: call `transform()` enough times to trigger JIT, observe the speedup with timing, and inspect JIT activity via JVM flags.

```java
// LifecycleJIT.java — observe JIT compilation via timing and JVM introspection
import java.lang.management.*;
import java.util.*;

public class LifecycleJIT {

    public static String transform(String input) {
        return input.trim().toUpperCase().replace(" ", "_");
    }

    // A heavier method to make JIT effect more visible
    public static long computeHash(String s) {
        long h = 1125899906842597L;
        for (int i = 0; i < s.length(); i++) h = 31 * h + s.charAt(i);
        return h;
    }

    public static void main(String[] args) throws Exception {
        System.out.println("=== JIT compilation demo ===\n");

        CompilationMXBean jit = ManagementFactory.getCompilationMXBean();
        System.out.println("JIT compiler: " + (jit != null ? jit.getName() : "none"));
        System.out.println("Total compile time at start: " +
            (jit != null ? jit.getTotalCompilationTime() : 0) + " ms\n");

        // Phase 1: first 100 calls — interpreted (cold)
        String[] inputs = {"hello world", "java se", "the quick brown fox"};
        long start = System.nanoTime();
        long sum = 0;
        for (int i = 0; i < 100; i++)
            sum += computeHash(transform(inputs[i % inputs.length]));
        long coldMs = (System.nanoTime() - start) / 1_000_000;

        long compileBefore = jit != null ? jit.getTotalCompilationTime() : 0;

        // Phase 2: 50,000 calls — JIT kicks in
        start = System.nanoTime();
        for (int i = 0; i < 50_000; i++)
            sum += computeHash(transform(inputs[i % inputs.length]));
        long warmMs = (System.nanoTime() - start) / 1_000_000;

        long compileAfter = jit != null ? jit.getTotalCompilationTime() : 0;

        // Phase 3: another 50,000 — fully JIT-compiled
        start = System.nanoTime();
        for (int i = 0; i < 50_000; i++)
            sum += computeHash(transform(inputs[i % inputs.length]));
        long hotMs = (System.nanoTime() - start) / 1_000_000;

        System.out.println("Timing (prevent dead-code elim: sum=" + (sum % 1000) + "):");
        System.out.printf("  Cold  (100 calls):    %d ms%n", coldMs);
        System.out.printf("  Warm  (50K calls):    %d ms  (JIT compiling)%n", warmMs);
        System.out.printf("  Hot   (50K more):     %d ms  (JIT done)%n", hotMs);
        System.out.printf("  JIT compile time in phase 2: %d ms%n", compileAfter - compileBefore);

        double speedup = warmMs > 0 ? (double) warmMs / Math.max(hotMs, 1) : 0;
        System.out.printf("  Speedup (warm→hot): ~%.1fx%n", speedup);

        System.out.println("\n[ Enable JIT logging ]");
        System.out.println("  java -XX:+PrintCompilation LifecycleJIT.java");
        System.out.println("  # prints a line each time a method gets JIT-compiled");
        System.out.println();
        System.out.println("  java -Xint LifecycleJIT.java");
        System.out.println("  # disable JIT — interpreted-only (slower, for comparison)");
        System.out.println();
        System.out.println("[ Lifecycle summary ]");
        System.out.println("  .java  → javac → .class (bytecode) → java → interpret → JIT → native");
    }
}
```

**How to run:** `java LifecycleJIT.java`

Run twice: first with `java LifecycleJIT.java`, then with `java -Xint LifecycleJIT.java` (`-Xint` disables JIT). The `-Xint` run will be noticeably slower for the Hot phase — that difference is the JIT's contribution. `CompilationMXBean.getTotalCompilationTime()` confirms JIT activity during the warm phase.

## 6. Walkthrough

Execution trace in `LifecycleRuntime.main`:

**Stage 1 — Source writing.** `Files.writeString(src, TRANSFORMER_SOURCE)` creates `RuntimeTransformer.java` in a temp directory. This is exactly what an IDE does when you press Ctrl+S.

**Stage 2 — Compile.** `compiler.run(null, null, null, src.toString())` calls `javac`. Return code 0 = success. `javac` reads the source, performs:
1. Lexical analysis: tokenise source characters.
2. Parsing: build AST (abstract syntax tree).
3. Semantic analysis: resolve types, check `String.trim()` exists on `String`, etc.
4. Code generation: emit bytecode instructions for each AST node.

`RuntimeTransformer.class` appears in the same directory as the source (default output). The magic header bytes `CA FE BA BE` and major version (`61` for JDK 17, `65` for JDK 21) are written into the first 8 bytes.

**Stage 3 — Load.** `URLClassLoader(new URL[]{work.toUri().toURL()})` tells the ClassLoader where to search for `.class` files. `loader.loadClass("RuntimeTransformer")` reads `RuntimeTransformer.class` bytes, verifies bytecode (checks type safety, no stack overflows, no illegal jumps), and creates a `Class<?>` object in the JVM's metaspace.

**Stage 3 — Execute.** `method.invoke(null, input)` calls `RuntimeTransformer.transform(input)`. The JVM starts in interpreted mode. The first ~1,000 calls run each bytecode instruction one-by-one. When the JIT's profiler detects the method is "hot" (invoked often), the C2 JIT compiler translates the bytecode to native x86/ARM machine code. Subsequent calls bypass bytecode interpretation entirely.

**Bytecode for `transform()`:**
```
aload_0          → push the String parameter onto the operand stack
invokevirtual    → call String.trim() (dispatches via vtable)
invokevirtual    → call String.toUpperCase()
ldc " "          → push constant " "
ldc "_"          → push constant "_"
invokevirtual    → call String.replace()
areturn          → return the String on top of stack
```

Each `invokevirtual` is a virtual method call — the JVM looks up the actual class's method table at runtime, which is why Java supports polymorphism.

## 7. Gotchas & takeaways

> **`java Hello.java` (JDK 11+ single-file launch) does NOT produce a visible `.class` file.** The launcher compiles to an in-memory bytecode representation and executes it directly. If you need the `.class` file (to deploy, inspect with `javap`, or share), use `javac Hello.java` explicitly.

> **Class file major version mismatch.** If you compile with JDK 21 (`major=65`) and deploy to a JRE 17 environment, the JVM throws `UnsupportedClassVersionError`. Fix with `javac --release 17 Hello.java` — this compiles to Java 17 bytecode even when using JDK 21. Maven uses `<maven.compiler.release>17</maven.compiler.release>` for the same purpose.

- `javac Hello.java` → `Hello.class` — always explicit compilation for anything beyond single-file scripts.
- `javap -c Hello.class` — inspect bytecode; useful for understanding performance and correctness.
- JIT kicks in after ~10,000 method invocations (C2 threshold, configurable with `-XX:CompileThreshold`).
- `-Xint` disables JIT (pure interpretation) — useful for benchmarking JIT impact.
- `-XX:+PrintCompilation` — prints each method as it gets JIT-compiled.
- `--release N` (javac flag) — target bytecode version for older JVM compatibility.
