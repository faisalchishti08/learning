---
card: java
gi: 33
slug: jshell-the-repl
title: jshell — the REPL
---

## 1. What it is

**`jshell`** is Java's interactive Read-Eval-Print Loop (REPL), introduced in Java 9 (JEP 222). It lets you type Java expressions, statements, and declarations and see the result immediately — without creating a class, writing a `main` method, or compiling a file.

`jshell` is part of `jdk.jshell` module, JDK-only. It accepts Java source at three levels: expressions (`2 + 2`), statements (`int x = 5;`), and declarations (`record Point(int x, int y) {}`). Everything typed in a jshell session is called a **snippet**.

## 2. Why & when

`jshell` is valuable for:
- **Exploring APIs** — quickly test what `String.format("%.2f", 3.14159)` returns without a project
- **Learning Java** — instant feedback loop for students
- **Debugging** — isolate a data-processing algorithm before integrating it
- **Documentation** — embedded `jshell` examples in docs are runnable snippets
- **Checking platform behaviour** — `Runtime.version().feature()` on a specific JDK

`jshell` is not a replacement for unit tests, but it removes the compilation overhead for quick experiments.

## 3. Core concept

jshell commands vs snippets:

```
jshell> 1 + 2                // expression snippet
$1 ==> 3

jshell> var s = "hello"      // variable declaration snippet
s ==> "hello"

jshell> s.toUpperCase()      // method invocation expression
$3 ==> "HELLO"

jshell> /list                // command (starts with /)
   1 : 1 + 2
   2 : var s = "hello"
   3 : s.toUpperCase()

jshell> /edit 2              // edit snippet #2 in editor
jshell> /drop 1              // remove snippet #1
jshell> /save session.jsh    // save snippets to file
jshell> /open session.jsh    // load and re-run a file
jshell> /exit                // quit
```

Key jshell commands:
| Command | Action |
|---------|--------|
| `/list` | Show all active snippets |
| `/vars` | Show declared variables |
| `/methods` | Show declared methods |
| `/types` | Show declared types |
| `/imports` | Show active imports |
| `/edit N` | Edit snippet N in external editor |
| `/drop N` | Remove snippet N |
| `/save file` | Save all snippets to file |
| `/open file` | Load and execute snippets from file |
| `/reset` | Reset — clear all snippets and state |
| `/help` | List all commands |
| `/env --add-modules M` | Add a module |
| `--class-path jar` | Add JAR to classpath (on startup) |

Default imports in jshell (no `import` needed):
- `java.lang.*`, `java.io.*`, `java.math.*`, `java.net.*`, `java.util.*`, `java.util.concurrent.*`, `java.util.function.*`, `java.util.prefs.*`, `java.util.regex.*`

## 4. Diagram

<svg viewBox="0 0 680 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="jshell REPL loop: user types snippet, evaluator compiles and runs, result printed">
  <rect x="10" y="10" width="660" height="180" rx="8" fill="#0d1117"/>

  <!-- REPL loop -->
  <circle cx="340" cy="100" r="70" fill="none" stroke="#6db33f" stroke-width="2"/>
  <text x="340" y="68" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">R-E-P-L loop</text>

  <!-- R -->
  <rect x="20"  y="75" width="100" height="40" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="70"  y="93" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Read</text>
  <text x="70"  y="107" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">user types snippet</text>

  <!-- E -->
  <rect x="270" y="20" width="140" height="40" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="340" y="38" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Eval</text>
  <text x="340" y="52" fill="#8b949e" font-size="8"  text-anchor="middle" font-family="sans-serif">compile + execute snippet</text>

  <!-- P -->
  <rect x="560" y="75" width="100" height="40" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="610" y="93" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Print</text>
  <text x="610" y="107" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">show result / error</text>

  <!-- L -->
  <rect x="270" y="140" width="140" height="40" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="340" y="158" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Loop</text>
  <text x="340" y="171" fill="#8b949e" font-size="8"  text-anchor="middle" font-family="sans-serif">back to Read</text>

  <!-- Arrows -->
  <path d="M120 95 Q200 60 270 40" fill="none" stroke="#8b949e" stroke-width="1.5" marker-end="url(#sh1)"/>
  <path d="M410 40 Q480 60 560 90" fill="none" stroke="#8b949e" stroke-width="1.5" marker-end="url(#sh1)"/>
  <path d="M560 115 Q480 155 410 155" fill="none" stroke="#8b949e" stroke-width="1.5" marker-end="url(#sh1)"/>
  <path d="M270 155 Q200 155 120 115" fill="none" stroke="#8b949e" stroke-width="1.5" marker-end="url(#sh1)"/>

  <defs>
    <marker id="sh1" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6" fill="none" stroke="#8b949e" stroke-width="1.5"/></marker>
  </defs>
</svg>

jshell REPL: Read (user types) → Eval (compile + execute) → Print (result/error) → Loop (repeat).

## 5. Runnable example

Scenario: use the `jshell` API programmatically to execute Java snippets and capture their results — the pattern used by notebook environments and interactive coding platforms.

### Level 1 — Basic

```java
// JShellBasic.java
// Shows what jshell interactive sessions look like (demonstrates jshell concepts)
public class JShellBasic {
    public static void main(String[] args) {
        System.out.println("=== jshell — Interactive Java REPL ===\n");
        System.out.println("Start jshell: jshell");
        System.out.println("Or: jshell --class-path extra.jar\n");

        System.out.println("Sample session:");
        System.out.println("─────────────────────────────────────────────");
        printSession(new String[][]{
            {"jshell>", "var x = 42",               "x ==> 42"},
            {"jshell>", "x * 2",                    "$2 ==> 84"},
            {"jshell>", "\"Hello\".repeat(3)",      "$3 ==> \"HelloHelloHello\""},
            {"jshell>", "record Point(int x, int y) {}", ""},
            {"jshell>", "var p = new Point(3, 4)",  "p ==> Point[x=3, y=4]"},
            {"jshell>", "Math.sqrt(p.x()*p.x() + p.y()*p.y())", "$6 ==> 5.0"},
            {"jshell>", "/vars",                    "  var x = 42\n  Point p = Point[x=3, y=4]"},
            {"jshell>", "/exit",                    ""},
        });
        System.out.println("─────────────────────────────────────────────");

        System.out.println("\nDefault imports (no import needed in jshell):");
        String[] defaults = {
            "java.lang.*", "java.io.*", "java.math.*",
            "java.net.*",  "java.util.*", "java.util.concurrent.*",
            "java.util.function.*", "java.util.regex.*"
        };
        for (String d : defaults) System.out.println("  import " + d);
    }

    static void printSession(String[][] lines) {
        for (var line : lines) {
            System.out.printf("%-10s %s%n", line[0], line[1]);
            if (!line[2].isEmpty()) {
                for (String r : line[2].split("\n")) System.out.println("  " + r);
            }
        }
    }
}
```

**How to run:** `java JShellBasic.java`

This shows what a jshell session looks like. To actually run jshell interactively, type `jshell` in a terminal with the JDK on your PATH.

### Level 2 — Intermediate

Same jshell demo extended to use the `jshell` API programmatically — executing snippets from code and capturing their status and values.

```java
// JShellApi.java
import jdk.jshell.*;
import java.util.List;

public class JShellApi {
    public static void main(String[] args) {
        // JShell API: execute snippets programmatically (used by IDEs, notebooks)
        try (JShell shell = JShell.create()) {
            System.out.println("=== JShell API Demo ===\n");

            List<String> snippets = List.of(
                "int x = 10",
                "int y = 20",
                "x + y",
                "var list = List.of(1, 2, 3, 4, 5)",
                "list.stream().filter(n -> n % 2 == 0).toList()",
                "record Person(String name, int age) {}",
                "new Person(\"Alice\", 30)",
                "\"hello world\".toUpperCase().replace(\" \", \"_\")"
            );

            for (String snippet : snippets) {
                System.out.printf(">>> %s%n", snippet);
                List<SnippetEvent> events = shell.eval(snippet);
                for (SnippetEvent event : events) {
                    Snippet s = event.snippet();
                    if (event.status() == Snippet.Status.VALID) {
                        if (event.value() != null && !event.value().isEmpty()) {
                            System.out.printf("    %s ==> %s%n",
                                s instanceof VarSnippet vs ? vs.name() : "$" + s.id(),
                                event.value());
                        }
                    } else if (event.status() == Snippet.Status.REJECTED) {
                        System.out.printf("    ERROR: %s%n",
                            shell.diagnostics(s).map(d -> d.getMessage(null)).findFirst().orElse("?"));
                    }
                }
            }

            System.out.println("\n[ Active variables ]");
            shell.variables().forEach(v ->
                System.out.printf("  %s %s = %s%n", v.typeName(), v.name(),
                    shell.varValue(v)));
        }
    }
}
```

**How to run:** `java JShellApi.java`

`JShell.create()` is the entry point. `shell.eval(snippet)` returns `List<SnippetEvent>` — one event per side-effect (variable creation, class definition, etc.). `SnippetEvent.value()` is the string representation of the evaluated expression.

### Level 3 — Advanced

Same JShell API grown to build a mini notebook executor: runs a list of snippets, tracks variable state across snippets, and detects errors with position information.

```java
// JShellNotebook.java
import jdk.jshell.*;
import jdk.jshell.Snippet.Status;
import java.util.*;
import java.util.stream.*;

public class JShellNotebook {

    record Cell(int num, String code, String output, boolean error) {}

    public static void main(String[] args) {
        // Notebook cells — each builds on the previous
        List<String> cells = List.of(
            // Cell 1: define data
            "var temps = List.of(22.5, 18.0, 25.1, 30.2, 19.8, 27.3, 24.0)",

            // Cell 2: compute stats using previous variable
            "var avg = temps.stream().mapToDouble(Double::doubleValue).average().orElse(0)",

            // Cell 3: filter
            "var aboveAvg = temps.stream().filter(t -> t > avg).toList()",

            // Cell 4: format report
            "String.format(\"Avg=%.1f°C, above-avg: %s\", avg, aboveAvg)",

            // Cell 5: intentional error
            "undefinedVariable + 1",

            // Cell 6: continues working after error
            "temps.stream().mapToDouble(Double::doubleValue).max().orElse(0)"
        );

        List<Cell> results = new ArrayList<>();

        try (JShell shell = JShell.builder()
                .executionEngine("local")  // run in same JVM process
                .build()) {

            for (int i = 0; i < cells.size(); i++) {
                String code = cells.get(i);
                StringBuilder out = new StringBuilder();
                boolean hasError = false;

                List<SnippetEvent> events = shell.eval(code);
                for (SnippetEvent event : events) {
                    if (event.status() == Status.REJECTED) {
                        hasError = true;
                        String msg = shell.diagnostics(event.snippet())
                            .map(d -> d.getMessage(null))
                            .collect(Collectors.joining("; "));
                        out.append("ERROR: ").append(msg);
                    } else if (event.exception() != null) {
                        hasError = true;
                        out.append("EXCEPTION: ").append(event.exception().getMessage());
                    } else if (event.value() != null && !event.value().isEmpty()) {
                        String name = event.snippet() instanceof VarSnippet vs ? vs.name() + " = " : "";
                        out.append(name).append(event.value());
                    }
                }

                results.add(new Cell(i + 1, code, out.toString(), hasError));
            }
        }

        // Print notebook
        System.out.println("╔══════════════════════════════════════════╗");
        System.out.println("║           JShell Notebook Output          ║");
        System.out.println("╚══════════════════════════════════════════╝\n");

        for (Cell cell : results) {
            System.out.printf("[%d] %s%n", cell.num(), cell.code());
            if (!cell.output().isEmpty()) {
                String indicator = cell.error() ? "  ✗ " : "  → ";
                System.out.println(indicator + cell.output());
            }
            System.out.println();
        }

        System.out.println("Note: variable state persists across cells — avg from cell 2 used in cell 3.");
    }
}
```

**How to run:** `java JShellApi.java` (also works as `java JShellNotebook.java`)

`JShell.builder().executionEngine("local")` runs snippets in the same JVM process for simplicity. The default mode uses a separate JVM for isolation. Tools like Jupyter Java kernels and Kotlin Notebook use the `JShell` API exactly this way.

## 6. Walkthrough

Execution in `JShellNotebook.main`:

1. **`JShell.builder().executionEngine("local").build()`** — the builder pattern. `executionEngine("local")` runs snippet bytecode in the same JVM (faster for demos; not safe for untrusted code). Default uses a subprocess.

2. **`shell.eval(code)`** — compiles and executes the snippet. Returns `List<SnippetEvent>`. Each event has:
   - `event.snippet()` — the compiled snippet object
   - `event.status()` — `VALID`, `REJECTED`, `DROPPED`
   - `event.value()` — string representation of the result (null for void)
   - `event.exception()` — if execution threw an exception

3. **Variable persistence** — `var temps = List.of(...)` in cell 1 creates a `VarSnippet`. Cell 3 references `avg` defined in cell 2. The `JShell` instance maintains a live symbol table across `eval()` calls — this is the "stateful" part of the REPL.

4. **Error recovery** — cell 5 (`undefinedVariable + 1`) is `REJECTED` (compile error). The jshell session continues normally for cell 6. Unlike a script, jshell doesn't abort on errors — each snippet is evaluated independently.

5. **`VarSnippet` cast** — `event.snippet() instanceof VarSnippet vs` uses a pattern variable to get the variable name. `VarSnippet.name()` returns `"temps"`, `"avg"`, etc. Expression snippets (no variable) get auto-names like `$3`.

## 7. Gotchas & takeaways

> **`jshell` is not a script runner** — it's an interactive tool. For running a `.jsh` script non-interactively use `jshell --startup PRINTING script.jsh`. For scripting a whole program, use `java Hello.java` (source-launch mode).

> **Unchecked exceptions print stack traces but don't exit jshell.** If `list.get(10)` throws `IndexOutOfBoundsException`, jshell shows the error and returns to the prompt — the session state is preserved. This is unlike a regular Java program where an uncaught exception terminates the process.

- `jshell` = REPL for Java; JDK 9+, in `jdk.jshell` module.
- No class/main needed; type expressions directly.
- Commands start with `/`: `/list`, `/vars`, `/methods`, `/open file.jsh`.
- Default imports include all of `java.util.*`, `java.lang.*`, etc.
- `JShell` API (`jdk.jshell.JShell`) enables programmatic snippet execution for IDEs and notebooks.
- `shell.variables()` lists active variables; `shell.varValue(v)` retrieves their current values.
