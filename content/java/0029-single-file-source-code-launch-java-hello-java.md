---
card: java
gi: 29
slug: single-file-source-code-launch-java-hello-java
title: Single-file source-code launch (java Hello.java)
---

## 1. What it is

**Single-file source-code launch** (JEP 330, Java 11) lets you run a `.java` file directly with `java Hello.java` without a separate `javac` step. The launcher compiles the source in memory to a temporary class and immediately executes it — no `.class` file is written to disk.

Java 21 (JEP 445) further adds **unnamed classes and instance main methods** as a preview feature: a top-level `void main()` without a class declaration compiles and runs, enabling `java Hello.java` to contain just `void main() { System.out.println("hi"); }`.

## 2. Why & when

Single-file launch suits:
- **Learning and experimentation** — no project setup, no `javac`, no classpath
- **Scripting** — Java as a scripting language; combine with a shebang line on Unix
- **Tutorials** — every example in this site runs with `java File.java`
- **Quick proofs-of-concept** — test a library without creating a Maven project

Limitations:
- Only the **first class** in the file is the launch target
- The source file is compiled into memory — no `.class` on disk
- Classpath JARs must be specified with `-cp` (same as `java`)
- Not suitable for multi-file projects — use `javac` + `java` or a build tool

## 3. Core concept

When `java Hello.java` is invoked:

```
1. java launcher detects the argument is a .java file
2. Compiles the source using javax.tools.JavaCompiler (in-memory)
3. Puts the compiled class into an in-memory classloader
4. Looks for the first top-level class in the file
5. Calls main(String[] args) on that class
   (or void main() / static void main() in Java 21 preview)
```

The classpath for the source-launch compilation includes:
- The JDK's standard library (always)
- Any `-cp` / `--class-path` you pass on the command line
- **Not** the directory containing the `.java` file itself

**Shebang support:** On Unix, a `.java` file with a shebang line runs as a script:

```java
#!/usr/bin/java --source 21
void main() {
    System.out.println("Java script!");
}
```

Make the file executable (`chmod +x script.java`) and run `./script.java`. The shebang must use `--source N` to avoid the `.java` extension check.

**Unnamed classes (Java 21 preview):** With `--enable-preview --source 21`, the top-level class declaration can be omitted:
```java
void main() {
    System.out.println("no class needed!");
}
```

## 4. Diagram

<svg viewBox="0 0 680 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Single-file launch: java Hello.java compiles in memory and runs immediately">
  <rect x="10" y="10" width="660" height="180" rx="8" fill="#0d1117"/>

  <!-- Normal path (top) -->
  <text x="30" y="38" fill="#8b949e" font-size="10" font-family="sans-serif">Normal flow:</text>
  <rect x="30" y="46" width="90" height="30" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="75" y="65" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Hello.java</text>
  <line x1="120" y1="61" x2="155" y2="61" stroke="#8b949e" stroke-width="1.5" marker-end="url(#sf1)"/>
  <rect x="155" y="46" width="80" height="30" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="195" y="65" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">javac</text>
  <line x1="235" y1="61" x2="270" y2="61" stroke="#8b949e" stroke-width="1.5" marker-end="url(#sf1)"/>
  <rect x="270" y="46" width="90" height="30" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="315" y="65" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Hello.class</text>
  <line x1="360" y1="61" x2="395" y2="61" stroke="#8b949e" stroke-width="1.5" marker-end="url(#sf1)"/>
  <rect x="395" y="46" width="80" height="30" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="435" y="65" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">java Hello</text>
  <line x1="475" y1="61" x2="510" y2="61" stroke="#8b949e" stroke-width="1.5" marker-end="url(#sf1)"/>
  <rect x="510" y="46" width="100" height="30" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="560" y="65" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">output</text>

  <!-- Single-file path (bottom) -->
  <text x="30" y="118" fill="#6db33f" font-size="10" font-family="sans-serif">Single-file launch:</text>
  <rect x="30" y="126" width="90" height="30" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="75" y="145" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">Hello.java</text>
  <line x1="120" y1="141" x2="155" y2="141" stroke="#6db33f" stroke-width="1.5" marker-end="url(#sf2)"/>
  <rect x="155" y="126" width="200" height="30" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="255" y="144" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">java launcher (compile+run)</text>
  <text x="255" y="154" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">in-memory .class, no disk write</text>
  <line x1="355" y1="141" x2="510" y2="141" stroke="#6db33f" stroke-width="1.5" marker-end="url(#sf2)"/>
  <rect x="510" y="126" width="100" height="30" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="560" y="145" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">output</text>

  <defs>
    <marker id="sf1" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6" fill="none" stroke="#8b949e" stroke-width="1.5"/></marker>
    <marker id="sf2" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6" fill="none" stroke="#6db33f" stroke-width="1.5"/></marker>
  </defs>
</svg>

Normal flow: `Hello.java` → `javac` → `Hello.class` → `java Hello`. Single-file: `java Hello.java` compiles in-memory and runs — no `.class` on disk.

## 5. Runnable example

Scenario: demonstrate single-file launch features — argument passing, classpath use, and the unnamed class preview syntax.

### Level 1 — Basic

```java
// SingleFileLaunch.java
// Run with: java SingleFileLaunch.java Alice 42
public class SingleFileLaunch {
    public static void main(String[] args) {
        System.out.println("=== Single-file source launch ===");
        System.out.println("Compiled and running without javac!");
        System.out.println("Java version : " + System.getProperty("java.version"));
        System.out.println();

        // Show how args work exactly like normal launch
        if (args.length == 0) {
            System.out.println("No args passed. Try: java SingleFileLaunch.java Alice 42");
        } else {
            System.out.println("Args received: " + args.length);
            for (int i = 0; i < args.length; i++) {
                System.out.printf("  args[%d] = \"%s\"%n", i, args[i]);
            }
        }

        // Key difference: no .class written to disk
        System.out.println("\nLook for .class file in this dir: none (compiled in-memory)");
    }
}
```

**How to run:** `java SingleFileLaunch.java` or `java SingleFileLaunch.java Alice 42`

Arguments after the filename are passed to `main(args)` exactly as with `java MyClass arg1 arg2`. Arguments before the filename (but after `java`) are JVM flags.

### Level 2 — Intermediate

Same single-file launch demo extended to show multiple class definitions in one file and how the first class rule works.

```java
// MultiClassSingleFile.java
// All classes in one file — only the first one can be public
// and its name doesn't need to match the filename in source-launch mode
import java.util.*;

// First class = the one with main() that gets invoked
class SingleFileDemo {
    public static void main(String[] args) {
        System.out.println("=== Multiple classes in one .java file ===\n");

        // Uses helper classes defined below in the same file
        var calc = new Calculator();
        System.out.println("sqrt(2)  = " + calc.sqrt(2.0));
        System.out.println("fact(10) = " + calc.factorial(10));

        var fmt = new PrettyPrinter();
        fmt.table(List.of(
            new String[]{"Operation", "Input", "Result"},
            new String[]{"sqrt",      "2",     String.valueOf(calc.sqrt(2.0))},
            new String[]{"sqrt",      "9",     String.valueOf(calc.sqrt(9.0))},
            new String[]{"factorial", "5",     String.valueOf(calc.factorial(5))},
            new String[]{"factorial", "10",    String.valueOf(calc.factorial(10))}
        ));

        System.out.println("\nNote: only '" + SingleFileDemo.class.getSimpleName()
            + "' can be public in a single file");
        System.out.println("Note: filename 'MultiClassSingleFile.java' != class name 'SingleFileDemo'");
        System.out.println("      This is fine in source-launch mode (javac would reject it)");
    }
}

// Helper classes in the same file — not public
class Calculator {
    double sqrt(double x) { return Math.sqrt(x); }
    long factorial(int n) {
        if (n <= 1) return 1;
        return n * factorial(n - 1);
    }
}

class PrettyPrinter {
    void table(List<String[]> rows) {
        int[] widths = new int[rows.get(0).length];
        for (var row : rows)
            for (int i = 0; i < row.length; i++)
                widths[i] = Math.max(widths[i], row[i].length());

        for (int r = 0; r < rows.size(); r++) {
            var row = rows.get(r);
            var sb = new StringBuilder("| ");
            for (int i = 0; i < row.length; i++) {
                sb.append(String.format("%-" + widths[i] + "s", row[i])).append(" | ");
            }
            System.out.println(sb);
            if (r == 0) {
                sb = new StringBuilder("|-");
                for (int w : widths) sb.append("-".repeat(w)).append("-|-");
                System.out.println(sb);
            }
        }
    }
}
```

**How to run:** `java MultiClassSingleFile.java`

In source-launch mode, the file can contain multiple non-public class definitions. The **first class definition** in the file is the one `java` looks for `main()` in — not the class whose name matches the filename.

### Level 3 — Advanced

Same multi-class file grown to demonstrate the JVM source-version flag, classpath use with external JARs, and how to use a shebang for scripting.

```java
// SourceLaunchFeatures.java
// Demonstrates: --source N flag, system properties, multiple classes, scripting patterns
import java.util.*;
import java.lang.management.*;

public class SourceLaunchFeatures {

    record SystemProperty(String key, String value) {
        static List<SystemProperty> selected(List<String> keys) {
            return keys.stream()
                .map(k -> new SystemProperty(k, System.getProperty(k, "n/a")))
                .toList();
        }
    }

    public static void main(String[] args) {
        System.out.println("╔══════════════════════════════════════════╗");
        System.out.println("║   Source-Launch Features Demo             ║");
        System.out.println("╚══════════════════════════════════════════╝");

        // 1. Version info
        var props = SystemProperty.selected(List.of(
            "java.version", "java.vm.name", "java.class.path"
        ));
        System.out.println("\n[ Runtime properties ]");
        props.forEach(p -> System.out.printf("  %-20s = %s%n", p.key(),
            p.value().length() > 60 ? p.value().substring(0, 60) + "..." : p.value()));

        // 2. Show how -cp works with source launch
        System.out.println("\n[ Adding JARs to source-launch classpath ]");
        System.out.println("  java -cp extra.jar SourceLaunchFeatures.java");
        System.out.println("  # -cp adds to the compile+run classpath");
        System.out.println("  # import com.example.ExternalClass works if extra.jar is on -cp");

        // 3. Shebang pattern
        System.out.println("\n[ Shebang scripting (Unix only) ]");
        System.out.println("  File: greet.java");
        System.out.println("  Content:");
        System.out.println("    #!/usr/bin/java --source 21");
        System.out.println("    void main() { System.out.println(\"Hello!\"); }");
        System.out.println("  Then: chmod +x greet.java && ./greet.java");

        // 4. Preview unnamed classes (show what the code looks like)
        System.out.println("\n[ Java 21+ unnamed class preview (--enable-preview --source 21) ]");
        System.out.println("  File content:");
        System.out.println("    void main() {");
        System.out.println("        System.out.println(\"No class declaration needed!\");");
        System.out.println("    }");
        System.out.println("  Run: java --enable-preview --source 21 unnamed.java");

        // 5. Key rule: first class wins
        System.out.println("\n[ First-class rule ]");
        System.out.println("  When multiple classes in one file, 'java' launches the FIRST one.");
        System.out.println("  This class: " + SourceLaunchFeatures.class.getSimpleName());

        // 6. Memory info
        Runtime rt = Runtime.getRuntime();
        System.out.printf("%n[ Memory after source-launch startup ]%n");
        System.out.printf("  Heap used : %.1f MB%n", (rt.totalMemory() - rt.freeMemory()) / 1e6);
        System.out.printf("  Heap max  : %.1f MB%n", rt.maxMemory() / 1e6);
    }
}
```

**How to run:** `java SourceLaunchFeatures.java`

`-cp` on the `java` command line applies to both the compilation and the runtime classpath — so external JARs are visible to both `javac` and the JVM in one flag.

## 6. Walkthrough

Execution in `SourceLaunchFeatures.main`:

1. **`SystemProperty.selected(List.of(...))`** — a record `SystemProperty` defined in the same class file holds a key-value pair. `System.getProperty(k, "n/a")` returns `"n/a"` for undefined properties. `java.class.path` in source-launch mode is often empty or the JDK internal path — the compiled class lives in an in-memory classloader, not on disk.

2. **`-cp` with source launch** — `java -cp extra.jar MyApp.java` makes `extra.jar` visible to both the in-memory javac compilation and the resulting runtime. This is how source-launch apps can use third-party libraries.

3. **Shebang pattern** — the JVM launcher ignores the first line if it starts with `#!`. The `--source 21` flag forces source-launch mode (normally triggered by the `.java` extension; the shebang strips the extension trigger).

4. **Unnamed classes** (JEP 445, preview in Java 21–23, permanent in Java 25+) — removes the requirement for a top-level class declaration in a single-file program. The compiler wraps the methods in an unnamed class automatically. `void main()` without `public static` also works as of Java 21 preview.

5. **`Runtime.getRuntime().totalMemory()`** — total heap memory currently allocated to the JVM (not `maxMemory()`). In source-launch mode, the JVM uses the same heap ergonomics as a normal launch — no additional memory for the in-memory compilation step stays resident after compilation.

## 7. Gotchas & takeaways

> **Source-launch mode uses in-memory compilation — no `.class` file on disk.** If you need the `.class` file (for inspection, jar packaging, or reuse without recompile), use `javac` explicitly.

> **The first class in the file must have `main(String[] args)`** (or `void main()` with preview). If you put a utility class first, source launch fails with `"Main method not found"`. Reorder so the class with `main` comes first.

- `java Hello.java` — source-launch, compiles in memory, no `.class` written (Java 11+).
- Multiple classes in one file: OK in source-launch; only the **first class** is the entry point.
- `-cp` applies to both the compilation and runtime classpath.
- Unnamed classes (`void main()` without class declaration) — preview in Java 21–23, permanent in Java 25+.
- Shebang (`#!/usr/bin/java --source 21`) enables Java files as Unix scripts.
- Filename does not need to match class name in source-launch mode (unlike `javac`).
