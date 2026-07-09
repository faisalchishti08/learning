---
card: java
gi: 638
slug: launch-single-file-source-programs
title: Launch single-file source programs
---

## 1. What it is

Java 11 introduced the ability to **run a single `.java` source file directly** without explicitly compiling it first — just `java MyProgram.java`. The JVM compiles the source in memory (using `javac` internally) and executes the resulting class in one step. This feature is designed for "shebang" scripts (`#!/path/to/java --source 11`), quick prototyping, and educational use — not for production deployment. It works for single-file programs that don't depend on other source files or external JARs (though `--class-path` can add JARs). The feature was enhanced in later Java versions: Java 17 allows `java MyProgram.java arg1 arg2`, and Java 21+ supports referencing multiple source files from a single launch file.

## 2. Why & when

The traditional Java workflow — write `.java`, run `javac`, run `java ClassName` — is a barrier to quick experimentation. It's also a barrier for newcomers who compare Java unfavourably to Python (`python script.py`), Node.js (`node script.js`), or Ruby (`ruby script.rb`). Single-file launch eliminates the compile step for simple programs, making Java feel more like a scripting language for small tasks. Use it for: quick prototyping, writing utility scripts, running code examples from tutorials (this very tutorial!), sharing runnable snippets with colleagues, and writing simple automation scripts where a full Maven/Gradle project would be overkill.

## 3. Core concept

```bash
# Before Java 11:
javac Hello.java    # compile to Hello.class
java Hello          # run the compiled class

# Java 11+:
java Hello.java     # compile AND run in one step

# With arguments:
java Hello.java Alice Bob

# As a shebang script (Unix/macOS):
#!/usr/bin/java --source 11
public class Hello {
    public static void main(String[] args) {
        System.out.println("Hello, " + args[0] + "!");
    }
}
```

The source file must contain exactly one top-level class (matching the file name). The class must have a `main(String[] args)` method. No package declaration is required (but it's allowed — the class is placed in that package for execution).

## 4. Diagram

<svg viewBox="0 0 560 130" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Single-file launch compiles in memory and executes directly">
  <rect x="10" y="10" width="540" height="110" rx="8" fill="#1c2430" stroke="#6db33f"/>

  <rect x="20" y="25" width="100" height="40" rx="4" fill="#0d1117" stroke="#f85149"/>
  <text x="70" y="43" fill="#f85149" font-size="10" text-anchor="middle" font-family="monospace">Old way</text>
  <text x="70" y="57" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">javac → java</text>

  <text x="135" y="50" fill="#8b949e" font-size="16" font-family="monospace" text-anchor="middle">→</text>

  <rect x="155" y="15" width="240" height="60" rx="4" fill="#0d1117" stroke="#3fb950"/>
  <text x="275" y="35" fill="#3fb950" font-size="10" text-anchor="middle" font-family="monospace">java Hello.java</text>
  <text x="275" y="50" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">One step: compile in memory → execute</text>
  <text x="275" y="63" fill="#8b949e" font-size="7" text-anchor="middle" font-family="monospace">No .class file left on disk (by default)</text>

  <text x="410" y="50" fill="#8b949e" font-size="16" font-family="monospace" text-anchor="middle">→</text>

  <rect x="430" y="25" width="110" height="40" rx="4" fill="#0d1117" stroke="#6db33f"/>
  <text x="485" y="47" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">Output!</text>
  <text x="485" y="60" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">program runs</text>

  <text x="20" y="100" fill="#8b949e" font-size="9" font-family="sans-serif">Limitations: single file only (in Java 11), no external .java dependencies, no unnamed classes (that's Java 21+)</text>
</svg>

The compilation step becomes invisible — `java Hello.java` does both compile and run in one command, making Java feel more like a scripting language for small programs.

## 5. Runnable example

Scenario: writing and running utility scripts — starting with a basic hello-world, extending to a script with arguments and shebang, and finally handling edge cases and limitations.

### Level 1 — Basic

```java
// File: HelloSingleFile.java
public class HelloSingleFile {
    public static void main(String[] args) {
        System.out.println("Hello from a single-file Java program!");
        System.out.println("No javac needed — just: java HelloSingleFile.java");
        System.out.println("Java version: " + System.getProperty("java.version"));
    }
}
```

**How to run:** `java HelloSingleFile.java`

Expected output:
```
Hello from a single-file Java program!
No javac needed — just: java HelloSingleFile.java
Java version: 17.0...
```

The simplest usage: a single-file program runs with one command. The JVM handles compilation transparently.

### Level 2 — Intermediate

```java
// File: GrepUtil.java
import java.io.*;
import java.nio.file.*;

/**
 * A simple grep-like utility — run as: java GrepUtil.java <pattern> <file>
 */
public class GrepUtil {
    public static void main(String[] args) throws IOException {
        if (args.length < 2) {
            System.out.println("Usage: java GrepUtil.java <pattern> <file>");
            System.out.println("Example: java GrepUtil.java NOTE notes.txt");
            return;
        }

        String pattern = args[0];
        Path file = Path.of(args[1]);

        if (!Files.exists(file)) {
            System.out.println("File not found: " + file);
            return;
        }

        System.out.println("Searching for '" + pattern + "' in " + file + ":
");

        // Read lines and filter
        Files.readString(file)
            .lines()
            .filter(line -> line.contains(pattern))
            .forEach(line -> {
                int idx = line.indexOf(pattern);
                // Highlight the match
                String highlighted = line.substring(0, idx) +
                    ">>>" + pattern + "<<<" +
                    line.substring(idx + pattern.length());
                System.out.println("  " + highlighted);
            });
    }
}
```

**How to run:** 
```
echo "Fix the login bug
NOTE: Add error handling
Update documentation
NOTE: Write tests" > notes.txt
java GrepUtil.java NOTE notes.txt
```

Expected output:
```
Searching for 'NOTE' in notes.txt:

  >>>NOTE<<<: Add error handling
  >>>NOTE<<<: Write tests
```

The real-world concern: utility scripts. This program reads a file, searches for a pattern, and highlights matches — a mini grep in ~30 lines. Running it requires no build tool, no JAR, no class file management. Pass arguments directly after the `.java` filename.

### Level 3 — Advanced

```java
// File: ScriptDemo.java
import java.io.*;
import java.nio.file.*;
import java.time.*;
import java.util.*;

/**
 * Demonstrates various single-file launch features and limitations.
 * Run: java ScriptDemo.java
 */
public class ScriptDemo {
    public static void main(String[] args) throws Exception {
        System.out.println("=== Single-file launch features ===\n");

        // 1. Multiple classes in the same file (inner or sibling)
        Helper.sayHello();

        // 2. Using the Java standard library (anything in java.*)
        System.out.println("Current time: " + LocalDateTime.now());
        System.out.println("OS: " + System.getProperty("os.name"));

        // 3. Command-line arguments
        System.out.println("Args received: " + Arrays.toString(args));

        // 4. File I/O (creating temp file, reading it back)
        Path temp = Files.createTempFile("demo", ".txt");
        Files.writeString(temp, "Temporary file created at: " + LocalDateTime.now());
        System.out.println("Temp file: " + temp);
        System.out.println("Content:  " + Files.readString(temp).trim());
        Files.deleteIfExists(temp);

        System.out.println("\n=== Limitations (Java 11) ===\n");
        System.out.println("❌ Cannot reference other .java files (single file only)");
        System.out.println("❌ Cannot use external JARs without --class-path");
        System.out.println("❌ No unnamed classes (that feature came in Java 21)");
        System.out.println("❌ Class name must match filename");
        System.out.println("\n=== Enhancements (Java 17+) ===\n");
        System.out.println("✅ Arguments after filename: java Prog.java arg1 arg2");
        System.out.println("✅ Shebang support: #!/usr/bin/java --source 17");
        System.out.println("✅ --source flag to specify version: java --source 11 Prog.java");

        System.out.println("\n=== Shebang example (save as 'hello' and chmod +x) ===\n");
        System.out.println("#!/usr/bin/java --source 11");
        System.out.println("public class HelloScript {");
        System.out.println("    public static void main(String[] args) {");
        System.out.println("        System.out.println(\"Hello from shebang!\");");
        System.out.println("    }");
        System.out.println("}");
    }
}

// Helper class in the same file (allowed for single-file launch)
class Helper {
    static void sayHello() {
        System.out.println("Helper says: Single-file programs can have multiple classes!");
    }
}
```

**How to run:** `java ScriptDemo.java arg1 arg2`

Expected output:
```
=== Single-file launch features ===

Helper says: Single-file programs can have multiple classes!
Current time: 2026-07-09T12:00:00
OS: Mac OS X
Args received: [arg1, arg2]
Temp file: /tmp/demo12345.txt
Content:  Temporary file created at: 2026-07-09T12:00:00

=== Limitations (Java 11) ===

❌ Cannot reference other .java files (single file only)
❌ Cannot use external JARs without --class-path
❌ No unnamed classes (that feature came in Java 21)
❌ Class name must match filename

=== Enhancements (Java 17+) ===

✅ Arguments after filename: java Prog.java arg1 arg2
✅ Shebang support: #!/usr/bin/java --source 17
✅ --source flag to specify version: java --source 11 Prog.java

=== Shebang example (save as 'hello' and chmod +x) ===

#!/usr/bin/java --source 11
public class HelloScript {
    public static void main(String[] args) {
        System.out.println("Hello from shebang!");
    }
}
```

The production-flavoured hard cases: (1) **Multiple classes** — single-file launch allows multiple non-public classes in the same file (like `Helper` above). Only one top-level public class matching the filename is required. (2) **Arguments** — `java Prog.java arg1 arg2` passes args to `main(String[])`. Arguments BEFORE the filename go to the JVM (e.g. `-Xmx`); arguments AFTER go to the program. (3) **Shebang scripts** — on Unix/macOS, a file starting with `#!/usr/bin/java --source 11` can be made executable (`chmod +x`) and run like any script. (4) **Limitations** — Java 11's single-file launch supports only one `.java` file. Java 17+ added `--source` flag. Java 21+ allows referencing multiple source files and supports unnamed classes (no `class` wrapper needed).

## 6. Walkthrough

Tracing `java HelloSingleFile.java`:

1. The user types `java HelloSingleFile.java` in a terminal. The `java` launcher detects that the argument ends with `.java` (rather than being a class name).

2. The launcher invokes `javac` (the Java compiler) **in-process** (no separate process spawned). The compiler reads `HelloSingleFile.java`, parses it, type-checks it, and generates bytecode in memory.

3. The bytecode is loaded directly into the JVM's class loader — no `.class` file is written to disk (by default). The class `HelloSingleFile` is defined in the runtime.

4. The launcher looks for `public static void main(String[] args)` in the loaded class. It invokes `HelloSingleFile.main(args)` with any command-line arguments passed after the filename.

5. The program executes normally — `System.out.println(...)` outputs to stdout, any exceptions propagate to the launcher, `System.exit()` terminates the JVM.

6. When `main` returns (or `System.exit` is called), the JVM shuts down. No `.class` file remains on disk.

The entire flow: `.java source → in-memory compilation → class loading → main invocation → execution → exit`. No intermediate files, no build step visible to the user.

## 7. Gotchas & takeaways

> Single-file launch in Java 11 is limited to **one source file** with no dependencies on other `.java` files. If your program imports another class you wrote in a separate file, it won't compile. For multi-file programs, use `javac` + `java` or a build tool. Java 21+ relaxes this with the ability to reference multiple source files.

- The feature is activated by passing a filename ending in `.java` to the `java` command. The JVM distinguishes this from a class name by the `.java` extension — so don't name your classes with a `.java` suffix.
- Memory compilation means no `.class` file clutter, but it also means the program is recompiled on every run (slight startup overhead). For frequently-run scripts, this overhead is negligible.
- Shebang scripts work on Unix/macOS: `#!/usr/bin/java --source 11` as the first line, followed by Java code. The `--source` flag is required for the shebang to work in Java 11–16. In Java 17+, `--source` is optional.
- Single-file programs can use the full JDK standard library (`java.*`, `javax.*`). They can also use external JARs with `--class-path` (or `-cp`).
- For production deployment, still compile to `.class` files or JARs — single-file launch is a development and scripting convenience, not a deployment model.
