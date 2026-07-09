---
card: java
gi: 769
slug: launch-multi-file-source-code-programs
title: Launch multi-file source-code programs
---

## 1. What it is

**Java 22** (JEP 458) extends the single-file source-code launcher (`java MyApp.java`, available since Java 11) to work across **multiple source files** in the same directory tree. Previously, `java SomeFile.java` could run a single `.java` file directly without a separate `javac` compilation step, but the moment that file referenced another class defined in a sibling `.java` file, the launcher couldn't find it and the program failed. Now, the launcher automatically locates and compiles other source files it needs from the same directory (and subdirectories) as the file you named, so a small multi-file program can still be run directly with `java Main.java`, without a manual build step or an explicit multi-file `javac` invocation.

## 2. Why & when

The single-file source launcher was designed for exactly the "quick script, one file, no ceremony" use case — and it succeeded at that, but it drew an artificial line right where many real quick scripts naturally want to grow: the moment you split one file into two for organization (a `Main.java` and a small `Helper.java`), you lost the ability to just run it directly and had to introduce an explicit `javac *.java && java Main` build step, right when the program was still small enough that a manual build step felt like disproportionate ceremony. This JEP removes that artificial cliff: `java Main.java` now looks in `Main.java`'s directory (and subdirectories) for any other source files the program needs, compiles them together in memory, and runs the result — meaning a small utility can grow from one file to a handful of files while staying in "just run it directly" mode the whole time, only graduating to a real build tool (Maven, Gradle) once it's grown enough to actually need one.

## 3. Core concept

```
project/
  Main.java
  Greeter.java
```

```java
// Main.java
void main() {
    Greeter greeter = new Greeter();
    System.out.println(greeter.greet("world"));
}
```

```java
// Greeter.java
class Greeter {
    String greet(String name) {
        return "Hello, " + name + "!";
    }
}
```

**How to run:** `java Main.java` (from inside `project/`) — the launcher finds `Greeter.java` automatically, compiles both files together in memory, and runs `Main`, with no separate `javac` step and no build file.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Running java Main.java now searches the same directory tree for other source files the program references, compiling all of them together in memory before running">
  <rect x="20" y="20" width="180" height="40" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="110" y="45" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">java Main.java</text>

  <line x1="200" y1="40" x2="250" y2="40" stroke="#79c0ff" stroke-width="2" marker-end="url(#arrow769)"/>
  <defs><marker id="arrow769" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker></defs>

  <rect x="260" y="20" width="200" height="40" rx="6" fill="#0f1620" stroke="#79c0ff"/>
  <text x="360" y="45" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">searches directory tree for referenced .java files</text>

  <line x1="460" y1="40" x2="510" y2="40" stroke="#79c0ff" stroke-width="2" marker-end="url(#arrow769)"/>

  <rect x="520" y="20" width="100" height="40" rx="6" fill="#0f1620" stroke="#8b949e"/>
  <text x="570" y="45" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">runs Main</text>

  <text x="320" y="120" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Finds Greeter.java, Utils.java, etc. automatically — compiled together in memory</text>
  <text x="320" y="150" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">No separate javac step, no build file, works for a small handful of files</text>
</svg>

*The launcher's automatic file discovery removes the cliff between "one file" and "needs a build tool."*

## 5. Runnable example

Scenario: a small command-line utility that grows from one file into three, staying directly runnable at every step.

### Level 1 — Basic

```java
// File: TempConverterBasic.java
void main() {
    double celsius = 20.0;
    double fahrenheit = celsius * 9.0 / 5.0 + 32;
    System.out.println(celsius + "C = " + fahrenheit + "F");
}
```

**How to run:** `java TempConverterBasic.java` (JDK 22+, using an implicitly declared class — see [implicitly declared classes (2nd preview)](0766-implicitly-declared-classes-instance-main-2nd-preview.md) — though the traditional `public class ... static void main` form works identically here).

This is a single-file program — the ordinary, already-established single-file source launcher use case.

### Level 2 — Intermediate

```java
// File: Main.java
void main() {
    TemperatureConverter converter = new TemperatureConverter();
    System.out.println(converter.celsiusToFahrenheit(20.0));
    System.out.println(converter.celsiusToFahrenheit(100.0));
}
```

```java
// File: TemperatureConverter.java (same directory as Main.java)
class TemperatureConverter {
    String celsiusToFahrenheit(double celsius) {
        double fahrenheit = celsius * 9.0 / 5.0 + 32;
        return celsius + "C = " + fahrenheit + "F";
    }
}
```

**How to run:** `java Main.java` (from the directory containing both files).

The real-world concern added: the program is now **split across two files**, `Main.java` and `TemperatureConverter.java`, purely for organizational clarity (separating the entry point from the conversion logic) — and it still runs with a single `java Main.java` command, the launcher automatically finding and compiling `TemperatureConverter.java` alongside it.

### Level 3 — Advanced

```java
// File: Main.java
import java.util.*;

void main(String[] args) {
    List<Double> celsiusValues = new ArrayList<>();
    for (String arg : args) {
        celsiusValues.add(ArgParser.parseTemperature(arg));
    }
    if (celsiusValues.isEmpty()) {
        celsiusValues.add(20.0); // default when no args given
    }

    TemperatureConverter converter = new TemperatureConverter();
    ReportPrinter printer = new ReportPrinter();
    for (double celsius : celsiusValues) {
        printer.printLine(converter.celsiusToFahrenheit(celsius));
    }
}
```

```java
// File: TemperatureConverter.java
class TemperatureConverter {
    String celsiusToFahrenheit(double celsius) {
        double fahrenheit = celsius * 9.0 / 5.0 + 32;
        return celsius + "C = " + fahrenheit + "F";
    }
}
```

```java
// File: ArgParser.java
class ArgParser {
    static double parseTemperature(String raw) {
        try {
            return Double.parseDouble(raw);
        } catch (NumberFormatException e) {
            System.out.println("skipping invalid temperature: " + raw);
            return Double.NaN;
        }
    }
}
```

```java
// File: ReportPrinter.java
class ReportPrinter {
    void printLine(String line) {
        System.out.println("  " + line);
    }
}
```

**How to run:** `java Main.java 20 100 not-a-number 0` (from the directory containing all four files).

This adds the production-flavored hard case: **four source files** — `Main`, `TemperatureConverter`, `ArgParser`, and `ReportPrinter` — each with a distinct responsibility, referenced from `Main.java`'s command-line-argument-driven `main`, and still launched with a single direct `java Main.java ...` command, no manual multi-file `javac` invocation and no build tool, even with a real command-line argument-parsing helper class in the mix.

## 6. Walkthrough

Tracing `java Main.java 20 100 not-a-number 0`:

1. The launcher parses `Main.java`, sees it references `ArgParser`, `TemperatureConverter`, and `ReportPrinter` — none of which are defined in `Main.java` itself — and searches the same directory (and subdirectories) for `.java` files that could define them, finding `ArgParser.java`, `TemperatureConverter.java`, and `ReportPrinter.java`.
2. All four files are compiled together **in memory** (no `.class` files are written to disk in the typical single/multi-file-launcher workflow), and `Main`'s `main(String[] args)` is invoked with `args = ["20", "100", "not-a-number", "0"]`.
3. The `for` loop calls `ArgParser.parseTemperature(arg)` for each argument. For `"20"`, `"100"`, and `"0"`, `Double.parseDouble` succeeds, returning `20.0`, `100.0`, and `0.0` respectively, each added to `celsiusValues`. For `"not-a-number"`, `Double.parseDouble` throws `NumberFormatException`, caught inside `parseTemperature`, which prints a skip message and returns `Double.NaN` — which still gets added to `celsiusValues` in this simplified version (a stricter version might filter `NaN` out before adding).
4. Since `celsiusValues` isn't empty, the default-value fallback is skipped.
5. For each value in `celsiusValues`, `converter.celsiusToFahrenheit(celsius)` computes and formats the conversion, and `printer.printLine(...)` prints it with a two-space indent.

Expected output:
```
skipping invalid temperature: not-a-number
  20.0C = 68.0F
  100.0C = 212.0F
  NaN C = NaN F
  0.0C = 32.0F
```

(The exact formatting of the `NaN` line depends on how string concatenation renders `Double.NaN`; the meaningful result is that the program runs correctly across four separate source files with a single direct launch command.)

## 7. Gotchas & takeaways

> **Gotcha:** this feature is specifically for the **source-launcher** workflow (`java Main.java`) — it does not replace `javac` or a build tool for anything beyond a small, single-directory collection of source files. Once a project needs external dependencies, a module system, separate compilation units for testing, or packaging into a distributable artifact, it has outgrown this feature and genuinely needs a real build tool.

- Extends the single-file source launcher (available since Java 11) to automatically discover and compile other `.java` files in the same directory tree.
- No build file, no manual `javac` step, and no explicit multi-file compile command needed — just `java Main.java`, exactly as with a single file.
- All referenced files are compiled together in memory for the run; nothing is written to disk as a side effect of running this way.
- Best suited for small utilities, scripts, and examples that have outgrown a single file but haven't yet grown enough to need Maven, Gradle, or a module system.
- Pairs naturally with [implicitly declared classes & instance main methods](0766-implicitly-declared-classes-instance-main-2nd-preview.md) — together, they let a small multi-file program stay entirely free of explicit class ceremony and build tooling until it genuinely needs either.
