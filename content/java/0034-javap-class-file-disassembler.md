---
card: java
gi: 34
slug: javap-class-file-disassembler
title: javap — class file disassembler
---

## 1. What it is

**`javap`** is the JDK class file disassembler. It reads a `.class` file and prints human-readable information about its contents: method signatures, field declarations, and optionally bytecode instructions. `javap` is part of `jdk.jdeps` module, JDK-only.

`javap` is the primary tool for understanding what the Java compiler actually produces, investigating library class signatures without source code, and debugging bytecode-level issues.

## 2. Why & when

`javap` matters when:
- **Understanding compilation output** — what bytecode does `for (int i : list)` generate vs a `for` loop? `javap -c` shows the difference.
- **Checking method signatures** — when you don't have source or Javadoc, `javap ClassName` shows public API.
- **Debugging `NoSuchMethodError` / `IncompatibleClassChangeError`** — the JVM error often quotes a method descriptor like `(Ljava/lang/String;I)V`; `javap` lets you verify what's actually in the class.
- **Verifying class file version** — `javap -verbose` shows `major version: 65` (= Java 21).
- **Understanding generics erasure** — `javap` shows the erased signature; `-verbose` shows the `Signature` attribute with generics.
- **Analysing lambda desugaring** — lambdas compile to `invokedynamic` opcodes and synthetic methods; `javap -p -c` shows them.

## 3. Core concept

Key `javap` flags:

```bash
javap [flags] classname-or-classfile

Basic (shows public members):
  javap java.util.ArrayList     # class name on classpath
  javap MyClass.class           # direct .class file path

Flags:
  -p / --private        show all members (including private)
  -c                    disassemble bytecode (Code attribute)
  -v / --verbose        full detail: constant pool, stack sizes, annotations
  -s                    show internal type descriptors
  -l                    show line number and local variable tables
  -constants            show static final constants

Common combos:
  javap -c MyClass.class         # bytecode only
  javap -v -p MyClass.class      # everything
  javap -c -p MyClass.class      # bytecode + private members
```

Reading bytecode output:
```
public int add(int, int);
  Code:
     0: iload_1       // push arg1 (first int param)
     1: iload_2       // push arg2 (second int param)
     2: iadd          // pop two ints, push sum
     3: ireturn       // return int on top of stack
```

Type descriptors in `javap -verbose` and error messages:
```
B  byte       C  char       D  double     F  float
I  int        J  long       S  short      Z  boolean
V  void       [  array
L<classname>; reference  (e.g. Ljava/lang/String;)

(Ljava/lang/String;I)V  = method taking String, int, returning void
([B)Ljava/lang/String;  = method taking byte[], returning String
```

## 4. Diagram

<svg viewBox="0 0 680 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="javap reading a .class file and outputting bytecode, signatures, constant pool">
  <rect x="10" y="10" width="660" height="190" rx="8" fill="#0d1117"/>

  <!-- Input -->
  <rect x="20" y="60" width="130" height="80" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="85" y="82"  fill="#e6edf3" font-size="11" text-anchor="middle" font-family="monospace">MyClass.class</text>
  <text x="85" y="98"  fill="#8b949e" font-size="8"  text-anchor="middle" font-family="sans-serif">magic · version</text>
  <text x="85" y="111" fill="#8b949e" font-size="8"  text-anchor="middle" font-family="sans-serif">constant pool</text>
  <text x="85" y="124" fill="#8b949e" font-size="8"  text-anchor="middle" font-family="sans-serif">methods + Code attr</text>

  <!-- javap -->
  <line x1="150" y1="100" x2="195" y2="100" stroke="#8b949e" stroke-width="1.5" marker-end="url(#jp1)"/>
  <rect x="195" y="78" width="100" height="44" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="245" y="100" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">javap</text>
  <text x="245" y="115" fill="#8b949e" font-size="8"  text-anchor="middle" font-family="sans-serif">-c -v -p</text>

  <!-- outputs -->
  <line x1="295" y1="100" x2="340" y2="100" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#jp2)"/>

  <rect x="340" y="30"  width="290" height="38" rx="4" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="485" y="47"  fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">public int add(int, int)</text>
  <text x="485" y="60"  fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">javap (no flags) — signatures only</text>

  <rect x="340" y="78"  width="290" height="52" rx="4" fill="#0d1117" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="355" y="96"  fill="#79c0ff" font-size="9" font-family="monospace">0: iload_1</text>
  <text x="355" y="110" fill="#79c0ff" font-size="9" font-family="monospace">1: iload_2</text>
  <text x="355" y="124" fill="#79c0ff" font-size="9" font-family="monospace">2: iadd</text>
  <text x="560" y="96"  fill="#8b949e" font-size="8" font-family="sans-serif">javap -c</text>

  <rect x="340" y="140" width="290" height="48" rx="4" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="355" y="158" fill="#6db33f" font-size="9" font-family="monospace">major version: 65 (Java 21)</text>
  <text x="355" y="172" fill="#6db33f" font-size="9" font-family="monospace">Constant pool: #1 = Utf8 add</text>
  <text x="560" y="158" fill="#8b949e" font-size="8" font-family="sans-serif">javap -v</text>

  <defs>
    <marker id="jp1" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6" fill="none" stroke="#8b949e" stroke-width="1.5"/></marker>
    <marker id="jp2" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6" fill="none" stroke="#79c0ff" stroke-width="1.5"/></marker>
  </defs>
</svg>

`javap` reads `.class` binary → outputs signatures (default), bytecode (`-c`), or full detail including constant pool and class file version (`-v`).

## 5. Runnable example

Scenario: compile a class to a temp file, run `javap` on it programmatically, and compare what different flag combinations show.

### Level 1 — Basic

```java
// JavapBasic.java
import java.io.*;
import java.nio.file.*;

public class JavapBasic {
    public static void main(String[] args) throws Exception {
        // Compile a simple target class
        Path tmpDir = Files.createTempDirectory("javap-demo");
        Path src = tmpDir.resolve("Calc.java");
        Files.writeString(src,
            "public class Calc {\n" +
            "    private int value;\n" +
            "    public Calc(int v) { this.value = v; }\n" +
            "    public int add(int x) { return value + x; }\n" +
            "    public static int square(int n) { return n * n; }\n" +
            "}\n");

        new ProcessBuilder("javac", src.toString())
            .directory(tmpDir.toFile()).redirectErrorStream(true).start().waitFor();

        Path classFile = tmpDir.resolve("Calc.class");
        System.out.println("=== javap demo (Calc.class) ===\n");

        // Run javap with different flags
        for (String[] flagSet : new String[][]{
            {"(default — public members)", new String[0]},
            {"-p (all members)", new String[]{"-p"}},
            {"-p -c (bytecode)", new String[]{"-p", "-c"}},
        }) {
            String label = flagSet[0];
            String[] flags = (String[]) flagSet[1];

            System.out.println("[ javap " + label + " ]");
            runJavap(classFile, flags);
            System.out.println();
        }

        Files.delete(classFile); Files.delete(src); Files.delete(tmpDir);
    }

    static void runJavap(Path classFile, String... extraFlags) throws Exception {
        Path javap = Path.of(System.getProperty("java.home")).resolve("bin/javap");
        String javapCmd = Files.exists(javap) ? javap.toString() :
            (Files.exists(Path.of(javap + ".exe")) ? javap + ".exe" : "javap");

        List<String> cmd = new java.util.ArrayList<>();
        cmd.add(javapCmd);
        cmd.addAll(java.util.Arrays.asList(extraFlags));
        cmd.add(classFile.toString());

        Process p = new ProcessBuilder(cmd).redirectErrorStream(true).start();
        System.out.println(new String(p.getInputStream().readAllBytes()));
        p.waitFor();
    }
}
```

**How to run:** `java JavapBasic.java`

`javap` without flags shows only public/protected members. `-p` shows everything including private fields. `-c` adds the bytecode.

### Level 2 — Intermediate

Same `javap` demo extended to disassemble a class with lambdas and show how lambda desugaring works at the bytecode level.

```java
// JavapLambda.java
import java.io.*;
import java.nio.file.*;
import java.util.*;

public class JavapLambda {
    public static void main(String[] args) throws Exception {
        Path tmpDir = Files.createTempDirectory("javap-lambda");
        Path src = tmpDir.resolve("Lambdas.java");
        Files.writeString(src,
            "import java.util.*;\n" +
            "import java.util.function.*;\n" +
            "public class Lambdas {\n" +
            "    public void demo() {\n" +
            "        // Lambda — compiles to invokedynamic + synthetic method\n" +
            "        Predicate<String> isLong = s -> s.length() > 5;\n" +
            "        Function<Integer, Integer> square = n -> n * n;\n" +
            "        Runnable task = () -> System.out.println(\"run\");\n" +
            "    }\n" +
            "}\n");

        Process compile = new ProcessBuilder("javac", src.toString())
            .directory(tmpDir.toFile()).redirectErrorStream(true).start();
        compile.waitFor();

        Path classFile = tmpDir.resolve("Lambdas.class");
        Path javap = findJavap();

        System.out.println("=== Lambda bytecode (javap -p -c Lambdas.class) ===\n");
        System.out.println("Key things to observe:");
        System.out.println("1. Lambda body compiles to a synthetic private static method");
        System.out.println("2. Lambda invocation uses 'invokedynamic' opcode");
        System.out.println("3. The LambdaMetafactory is wired up at runtime via BootstrapMethod\n");

        Process p = new ProcessBuilder(javap, "-p", "-c", classFile.toString())
            .redirectErrorStream(true).start();
        String out = new String(p.getInputStream().readAllBytes());
        p.waitFor();

        // Highlight key lines
        for (String line : out.split("\n")) {
            if (line.contains("invokedynamic") || line.contains("lambda$") ||
                line.contains("synthetic") || line.contains("BootstrapMethod")) {
                System.out.println("  >>> " + line.strip());
            } else {
                System.out.println("      " + line);
            }
        }

        Files.delete(classFile); Files.delete(src); Files.delete(tmpDir);
    }

    static String findJavap() {
        Path javap = Path.of(System.getProperty("java.home")).resolve("bin/javap");
        if (Files.exists(javap)) return javap.toString();
        if (Files.exists(Path.of(javap + ".exe"))) return javap + ".exe";
        return "javap";
    }
}
```

**How to run:** `java JavapLambda.java`

Lambdas desugar to: (1) a synthetic private static method containing the lambda body, and (2) an `invokedynamic` instruction that uses `LambdaMetafactory` to create the functional interface instance at runtime. `javap -p -c` reveals both.

### Level 3 — Advanced

Same scenario grown to parse `javap -verbose` output and extract class file metadata: version, constant pool size, method signatures with type descriptors.

```java
// JavapVerboseParser.java
import java.io.*;
import java.nio.file.*;
import java.util.*;
import java.util.regex.*;

public class JavapVerboseParser {
    public static void main(String[] args) throws Exception {
        Path tmpDir = Files.createTempDirectory("javap-verbose");
        Path src = tmpDir.resolve("Service.java");
        Files.writeString(src,
            "import java.util.*;\n" +
            "public class Service {\n" +
            "    private final List<String> items = new ArrayList<>();\n" +
            "    public void add(String item) { items.add(item); }\n" +
            "    public List<String> getAll() { return Collections.unmodifiableList(items); }\n" +
            "    public static <T extends Comparable<T>> T max(List<T> list) {\n" +
            "        return Collections.max(list);\n" +
            "    }\n" +
            "}\n");

        new ProcessBuilder("javac", src.toString())
            .directory(tmpDir.toFile()).redirectErrorStream(true).start().waitFor();

        Path classFile = tmpDir.resolve("Service.class");
        String javap = findJavap();

        // Get verbose output
        Process p = new ProcessBuilder(javap, "-verbose", "-p", classFile.toString())
            .redirectErrorStream(true).start();
        String verbose = new String(p.getInputStream().readAllBytes());
        p.waitFor();

        System.out.println("=== Parsed javap -verbose output ===\n");

        // Extract class file version
        Matcher versionMatcher = Pattern.compile("major version: (\\d+)").matcher(verbose);
        if (versionMatcher.find()) {
            int major = Integer.parseInt(versionMatcher.group(1));
            System.out.printf("Class file version: major=%d (JDK %d)%n", major, major - 44);
        }

        // Extract constant pool count
        Matcher cpMatcher = Pattern.compile("Constant pool:\\n(?:.*\\n)*?(?=\\{)").matcher(verbose);
        long cpEntries = verbose.lines()
            .filter(l -> l.matches("\\s+#\\d+ = .*"))
            .count();
        System.out.printf("Constant pool entries: %d%n", cpEntries);

        // Extract method descriptors
        System.out.println("\nMethod descriptors (type erasure visible):");
        verbose.lines()
            .filter(l -> l.contains("descriptor:"))
            .map(String::strip)
            .forEach(l -> System.out.println("  " + l));

        // Extract generic signatures (pre-erasure type info)
        System.out.println("\nGeneric Signature attributes (original type params):");
        boolean inSig = false;
        for (String line : verbose.split("\n")) {
            if (line.contains("Signature:")) inSig = true;
            if (inSig && line.contains("#") && line.contains("//")) {
                System.out.println("  " + line.strip());
                inSig = false;
            }
        }

        // Show type descriptor legend
        System.out.println("\nType descriptor legend:");
        System.out.println("  B=byte  C=char  D=double  F=float  I=int  J=long  S=short  Z=boolean");
        System.out.println("  V=void  [=array  L<classname>;=reference");
        System.out.println("  (I)V = takes int, returns void");
        System.out.println("  (Ljava/lang/String;)Z = takes String, returns boolean");

        Files.delete(classFile); Files.delete(src); Files.delete(tmpDir);
    }

    static String findJavap() {
        Path javap = Path.of(System.getProperty("java.home")).resolve("bin/javap");
        if (Files.exists(javap)) return javap.toString();
        if (Files.exists(Path.of(javap + ".exe"))) return javap + ".exe";
        return "javap";
    }
}
```

**How to run:** `java JavapVerboseParser.java`

`javap -verbose` shows the full constant pool including the `#N = Utf8 "value"` entries, method descriptors (after type erasure), and `Signature` attributes (pre-erasure generic type information stored as a separate attribute).

## 6. Walkthrough

Execution in `JavapVerboseParser.main`:

1. **Compilation** — `ProcessBuilder("javac", src.toString())` compiles `Service.java`. The source has generics (`List<String>`, `<T extends Comparable<T>>`).

2. **`javap -verbose`** output sections:
   - Header: class name, flags, superclass
   - `minor version: 0` / `major version: 65` → class file version
   - `Constant pool`: all string literals, class names, method refs used in bytecode
   - For each field/method: descriptor (erased), signature attribute (generic), flags, Code attribute

3. **Type erasure in descriptors** — `getAll()` returns `List<String>` in source but `descriptor: ()Ljava/util/List;` in bytecode — the `<String>` is erased. The `Signature: ()Ljava/util/List<Ljava/lang/String;>;` attribute preserves the original generic type for reflection (`Method.getGenericReturnType()`).

4. **`NoSuchMethodError` debugging** — if you see `NoSuchMethodError: Service.max(Ljava/util/List;)Ljava/lang/Comparable;`, that's the erased descriptor. `javap -verbose Service.class` lets you verify what method is actually in the class file vs what the caller expects.

5. **Lambda synthetic methods** — `javap -p` reveals `private static lambda$demo$0(Ljava/lang/String;)Z` — the compiler-generated static method containing the lambda body. The `$0` counter increments for each lambda in the class.

## 7. Gotchas & takeaways

> **`javap` reads class files, not source files.** If you see a different method signature than you expect, make sure you're disassembling the newly compiled class, not a cached old one in a build directory. `find . -name "*.class" | xargs rm` + recompile resolves stale-class confusion.

> **Type descriptors encode everything the JVM needs.** `(Ljava/lang/String;[BI)V` is a method taking `String`, `byte[]`, `int`, returning `void`. Understanding descriptors is essential for reading `NoSuchMethodError` and `NoSuchFieldError` messages in stack traces.

- `javap ClassName` — public signatures only (no bytecode).
- `javap -c` — adds bytecode disassembly.
- `javap -v -p` — full detail: version, constant pool, all members, generics.
- Lambdas → `invokedynamic` + synthetic static method containing the body.
- Type descriptors: `I`=int, `Z`=boolean, `L...;`=reference, `[`=array, `V`=void.
- Generics are erased in descriptors; the `Signature` attribute preserves original generic types.
