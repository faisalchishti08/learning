---
card: java
gi: 606
slug: jshell-repl
title: JShell REPL
---

## 1. What it is

JShell is a **R**ead-**E**val-**P**rint-**L**oop (REPL) tool introduced in Java 9. It provides an interactive command-line environment where you can type Java statements, expressions, and declarations, and see their results immediately — no class, no `main` method, no compilation step required. JShell evaluates each snippet as you type it, prints the result, and keeps the accumulated state (variables, methods, classes) alive for subsequent snippets. It is accessed via the `jshell` command.

## 2. Why & when

Java has always required a certain ceremony: a file, a class, a `main` method, `javac`, then `java`. This is appropriate for production code but heavy for exploration, learning, prototyping, and quick experiments. Before JShell, Java developers who wanted to test a one-line expression or explore an unfamiliar API had to either create a throwaway file or use an IDE's "scrapbook" feature. JShell brings the immediacy of Python's or JavaScript's interactive consoles to Java, dramatically lowering the barrier to experimentation. It is especially useful for: exploring new APIs, teaching Java (immediate feedback), prototyping algorithms, and debugging by interactively calling methods with test data.

## 3. Core concept

```
$ jshell
|  Welcome to JShell -- Version 17
|  For an introduction type: /help intro

jshell> int x = 5
x ==> 5

jshell> x * 2
$2 ==> 10

jshell> String greet(String name) { return "Hello, " + name; }
|  created method greet(String)

jshell> greet("World")
$4 ==> "Hello, World"

jshell> /exit
|  Goodbye
```

Each snippet is assigned a variable (`$2`, `$4`) that holds its value for reference. You can declare variables (`int x = 5`), methods (`String greet(...)`), classes, imports, and expressions — all without a wrapping class. Terminal semicolons are optional for expressions (they are inferred). `/` commands (like `/exit`, `/list`, `/vars`, `/methods`) control the JShell session.

## 4. Diagram

<svg viewBox="0 0 560 180" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="JShell REPL loop: read snippet → eval → print result → repeat">
  <rect x="20" y="10" width="520" height="160" rx="8" fill="#1c2430" stroke="#6db33f"/>

  <rect x="60" y="30" width="140" height="40" rx="4" fill="#0d1117" stroke="#79c0ff"/>
  <text x="130" y="55" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="monospace">READ: type Java</text>

  <text x="215" y="55" fill="#8b949e" font-size="11" font-family="monospace">→</text>

  <rect x="230" y="30" width="140" height="40" rx="4" fill="#0d1117" stroke="#6db33f"/>
  <text x="300" y="55" fill="#6db33f" font-size="12" text-anchor="middle" font-family="monospace">EVAL: compile &amp; run</text>

  <text x="385" y="55" fill="#8b949e" font-size="11" font-family="monospace">→</text>

  <rect x="400" y="30" width="130" height="40" rx="4" fill="#0d1117" stroke="#f0883e"/>
  <text x="465" y="55" fill="#f0883e" font-size="12" text-anchor="middle" font-family="monospace">PRINT: result</text>

  <text x="540" y="55" fill="#8b949e" font-size="11" font-family="monospace">↻</text>

  <text x="60" y="105" fill="#8b949e" font-size="10" font-family="sans-serif">Key commands:</text>
  <text x="60" y="123" fill="#6db33f" font-size="10" font-family="monospace">  /list       — show all snippets</text>
  <text x="60" y="140" fill="#6db33f" font-size="10" font-family="monospace">  /vars       — list declared variables</text>
  <text x="60" y="157" fill="#6db33f" font-size="10" font-family="monospace">  /methods    — list declared methods</text>
  <text x="300" y="123" fill="#6db33f" font-size="10" font-family="monospace">  /edit       — open in external editor</text>
  <text x="300" y="140" fill="#6db33f" font-size="10" font-family="monospace">  /save       — save session to file</text>
  <text x="300" y="157" fill="#6db33f" font-size="10" font-family="monospace">  /open       — load snippets from file</text>
</svg>

JShell maintains in-memory state across snippets — variables and methods persist until the session ends.

## 5. Runnable example

Scenario: interactive exploration of Java collections and streams — starting with basic variable declaration and expression evaluation, extending to method definition and API exploration, and finally building a complete prototype with saved/loaded snippets.

### Level 1 — Basic

```java
// File: JShellDemo.java (runs as a normal program, simulating JShell output)
public class JShellDemo {
    public static void main(String[] args) {
        System.out.println("=== Simulated JShell Session ===\n");

        int x = 42;
        System.out.println("jshell> int x = 42");
        System.out.println("x ==> 42\n");

        String name = "Java";
        System.out.println("jshell> String name = \"Java\"");
        System.out.println("name ==> \"Java\"\n");

        System.out.println("jshell> x + 10");
        System.out.println("$3 ==> " + (x + 10) + "\n");

        System.out.println("jshell> name.length()");
        System.out.println("$4 ==> " + name.length() + "\n");

        System.out.println("jshell> name.toUpperCase()");
        System.out.println("$5 ==> \"" + name.toUpperCase() + "\"\n");

        System.out.println("jshell> /exit");
        System.out.println("|  Goodbye");
    }
}
```

**How to run:** `java JShellDemo.java`

Expected output:
```
=== Simulated JShell Session ===

jshell> int x = 42
x ==> 42

jshell> String name = "Java"
name ==> "Java"

jshell> x + 10
$3 ==> 52

jshell> name.length()
$4 ==> 4

jshell> name.toUpperCase()
$5 ==> "JAVA"

jshell> /exit
|  Goodbye
```

The simplest session: declare variables, evaluate expressions, explore API methods. Each result is printed with an auto-generated variable name (`$3`, `$4`). This is what you'd see in an actual `jshell` terminal — the simulation is necessary because a `.java` file always runs as a compile-then-execute program.

### Level 2 — Intermediate

```java
// File: JShellAdvanced.java
import java.util.*;
import java.util.stream.*;

public class JShellAdvanced {
    public static void main(String[] args) {
        System.out.println("=== Advanced JShell Session ===\n");

        // --- Declare a method ---
        System.out.println("jshell> List<Integer> squares(int n) {");
        System.out.println("   ...>     return IntStream.rangeClosed(1, n)");
        System.out.println("   ...>         .map(i -> i * i)");
        System.out.println("   ...>         .boxed().toList();");
        System.out.println("   ...> }");
        System.out.println("|  created method squares(int)\n");

        // --- Call it ---
        List<Integer> result = IntStream.rangeClosed(1, 5)
            .map(i -> i * i)
            .boxed()
            .toList();
        System.out.println("jshell> squares(5)");
        System.out.println("$2 ==> " + result + "\n");

        // --- Declare a record ---
        System.out.println("jshell> record Point(int x, int y) {}");
        System.out.println("|  created record Point\n");

        // --- Use it ---
        System.out.println("jshell> var p = new Point(3, 4)");
        System.out.println("p ==> Point[x=3, y=4]\n");

        // --- List variables and methods ---
        System.out.println("jshell> /vars");
        System.out.println("|    List<Integer> $2 = " + result);
        System.out.println("|    Point p = Point[x=3, y=4]\n");

        System.out.println("jshell> /methods");
        System.out.println("|    List<Integer> squares(int)\n");

        System.out.println("jshell> /exit");
        System.out.println("|  Goodbye");
    }
}
```

**How to run:** `java JShellAdvanced.java`

Expected output:
```
=== Advanced JShell Session ===

jshell> List<Integer> squares(int n) {
   ...>     return IntStream.rangeClosed(1, n)
   ...>         .map(i -> i * i)
   ...>         .boxed().toList();
   ...> }
|  created method squares(int)

jshell> squares(5)
$2 ==> [1, 4, 9, 16, 25]

jshell> record Point(int x, int y) {}
|  created record Point

jshell> var p = new Point(3, 4)
p ==> Point[x=3, y=4]

jshell> /vars
|    List<Integer> $2 = [1, 4, 9, 16, 25]
|    Point p = Point[x=3, y=4]

jshell> /methods
|    List<Integer> squares(int)

jshell> /exit
|  Goodbye
```

The real-world concern added: JShell supports multi-line snippets (you type `{` and JShell enters continuation mode `...>` until you close it). You can declare methods, records, classes, enums, and interfaces — all interactively. `/vars` and `/methods` list the currently declared state. This is the workflow for prototyping: declare a method, call it with test data, tweak and redeclare, repeat.

### Level 3 — Advanced

```java
// File: JShellScriptDemo.java
import java.io.*;
import java.nio.file.*;
import java.time.*;
import java.util.stream.*;

public class JShellScriptDemo {
    public static void main(String[] args) throws Exception {
        // Write a JShell script file (can be loaded with: jshell script.jsh)
        Path script = Path.of("/tmp/demo.jsh");
        String content = """
            // JShell script: process-data.jsh
            // Load with: jshell process-data.jsh

            import java.time.*;
            import java.util.stream.*;

            // Generate a list of dates
            var start = LocalDate.of(2026, 7, 1);
            var dates = Stream.iterate(start, d -> d.isBefore(LocalDate.of(2026, 8, 1)), d -> d.plusDays(1))
                .toList();
            System.out.println("Generated " + dates.size() + " dates from " + start);

            // Find all Mondays
            var mondays = dates.stream()
                .filter(d -> d.getDayOfWeek() == DayOfWeek.MONDAY)
                .toList();
            System.out.println("Mondays: " + mondays);

            System.out.println("\\n--- Session State ---");
            System.out.println("/vars output would show dates and mondays");
            """;
        Files.writeString(script, content);

        System.out.println("Script written to: " + script);
        System.out.println("\nRun with:  jshell " + script + "\n");

        System.out.println("=== Script content ===");
        System.out.println(content);

        // Simulate what JShell would output
        System.out.println("\n=== JShell output (simulated) ===");
        var start = LocalDate.of(2026, 7, 1);
        var dates = Stream.iterate(start, d -> d.isBefore(LocalDate.of(2026, 8, 1)), d -> d.plusDays(1))
            .toList();
        System.out.println("Generated " + dates.size() + " dates from " + start);

        var mondays = dates.stream()
            .filter(d -> d.getDayOfWeek() == DayOfWeek.MONDAY)
            .toList();
        System.out.println("Mondays: " + mondays);

        // Cleanup
        Files.deleteIfExists(script);
    }
}
```

**How to run:** `java JShellScriptDemo.java`

Expected output:
```
Script written to: /tmp/demo.jsh

Run with:  jshell /tmp/demo.jsh

=== Script content ===
// JShell script: process-data.jsh
// Load with: jshell process-data.jsh

import java.time.*;
import java.util.stream.*;

var start = LocalDate.of(2026, 7, 1);
var dates = Stream.iterate(start, d -> d.isBefore(LocalDate.of(2026, 8, 1)), d -> d.plusDays(1))
    .toList();
System.out.println("Generated " + dates.size() + " dates from " + start);

var mondays = dates.stream()
    .filter(d -> d.getDayOfWeek() == DayOfWeek.MONDAY)
    .toList();
System.out.println("Mondays: " + mondays);

System.out.println("\n--- Session State ---");
System.out.println("/vars output would show dates and mondays");

=== JShell output (simulated) ===
Generated 31 dates from 2026-07-01
Mondays: [2026-07-06, 2026-07-13, 2026-07-20, 2026-07-27]
```

The production-flavoured workflow: JShell scripts (`.jsh` files) can be saved and loaded across sessions. This example writes a script to disk, shows the content, and simulates what `jshell process-data.jsh` would output. In practice, you can use `/save file.jsh` to persist your session, `/open file.jsh` to replay it later, and even use JShell as a `#!` shebang script (`#!/usr/bin/jshell --execution local`) for scripting purposes.

## 6. Walkthrough

Tracing a `jshell` session with the script from Level 3:

1. User runs `jshell /tmp/demo.jsh` at the terminal. JShell starts and reads the file line by line.

2. **Import statements**: `import java.time.*;` and `import java.util.stream.*;` are processed. These imports become available for all subsequent snippets in the session.

3. **Variable declaration**: `var start = LocalDate.of(2026, 7, 1);` — JShell compiles and executes this snippet. A variable `start` of type `LocalDate` is added to the session state. Output: `start ==> 2026-07-01`.

4. **Stream expression**: `var dates = Stream.iterate(start, ..., d -> d.plusDays(1)).toList();` — This is a multi-part snippet. JShell compiles it as a whole. The stream generates 31 dates (July 1–31), collects them into a list, and assigns to `dates`. Output: `dates ==> [2026-07-01, 2026-07-02, ..., 2026-07-31]`.

5. **Print statement**: `System.out.println(...)` — prints `"Generated 31 dates from 2026-07-01"`. JShell does not print an auto-variable for statements that return `void`.

6. **Filter expression**: `var mondays = dates.stream().filter(...).toList();` — filters the 31 dates for Mondays. Output: `mondays ==> [2026-07-06, 2026-07-13, 2026-07-20, 2026-07-27]`.

7. **Second print**: Prints the Monday list.

8. **Footer prints**: The script prints additional lines. When the file ends, JShell returns to the interactive prompt — the session state (`start`, `dates`, `mondays`) is still alive and can be queried with `/vars`, modified, or extended.

```
$ jshell /tmp/demo.jsh
|  Welcome to JShell
jshell> (from file) var start = LocalDate.of(2026,7,1);
start ==> 2026-07-01

jshell> (from file) var dates = Stream.iterate(...).toList();
dates ==> [2026-07-01, ... 31 elements ...]

jshell> (from file) System.out.println("Generated 31 dates...");
Generated 31 dates from 2026-07-01

jshell> (from file) var mondays = dates.stream()...;
mondays ==> [2026-07-06, 2026-07-13, 2026-07-20, 2026-07-27]

jshell> (from file) System.out.println("Mondays: ...");
Mondays: [2026-07-06, 2026-07-13, 2026-07-20, 2026-07-27]

jshell> /vars       ← still interactive!
|    LocalDate start = 2026-07-01
|    List<LocalDate> dates = [31 elements]
|    List<LocalDate> mondays = [4 elements]
```

## 7. Gotchas & takeaways

> JShell evaluates snippets in a **single JVM instance** — all declarations share the same classpath, and side effects from one snippet (e.g. modifying a static field or opening a file) are visible to all subsequent snippets. This is powerful for prototyping but means a mistake in one snippet can corrupt the session state. Use `/reset` to start a fresh session without exiting.

- Semicolons are **optional** in JShell for expression statements — typing `x + 1` is sufficient; you don't need `x + 1;`. For declarations (variables, methods, classes), the semicolon is still required (or JShell infers the end at `}`).
- JShell uses a **different compilation model** than `javac` — each snippet is compiled as a separate "wrapper" class internally, which means some compile-time checks (like exhaustive switch on sealed classes) may behave slightly differently than in `.java` file compilation.
- `/edit` opens the current snippet or all snippets in an external editor (specified by the `JSHELL_EDITOR` environment variable or `$EDITOR`), enabling comfortable editing of multi-line declarations.
- JShell can run with **custom execution engines** via `--execution local` (direct execution in the same JVM, fastest), `--execution jdi` (separate JVM via JDI, more isolation), or custom engines for specialised environments.
- Tab completion works in JShell — type `System.out.` and press Tab to see available methods; type `/` and press Tab to see available commands. This makes API exploration extremely efficient. 