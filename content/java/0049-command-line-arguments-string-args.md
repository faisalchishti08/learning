---
card: java
gi: 49
slug: command-line-arguments-string-args
title: Command-line arguments (String[] args)
---

## 1. What it is

**Command-line arguments** are strings you pass to a Java program when running it from the terminal. The JVM collects every token after the class/JAR name and delivers them to `main` as a `String[]` called `args`:

```bash
java MyApp hello world 42
#          args[0]  args[1] args[2]
```

Inside `main`, `args.length` is the count and `args[0]` through `args[args.length-1]` are the values — always as `String`, even when the user types a number.

## 2. Why & when

Command-line arguments are the simplest way to configure a program at launch time without modifying code. Use them when:
- **Running a one-off tool**: `java Convert input.csv output.json`
- **Selecting behaviour**: `java Server --port 8080 --env prod`
- **Scripting and CI**: shell scripts pass arguments to control what the program does.

Alternatives:
- **Environment variables** (`System.getenv`) — for secrets and platform config that shouldn't be on the command line (visible in `ps` output).
- **Config files** — for complex structured configuration.
- **System properties** (`-Djava.property=value`) — JVM-level flags, readable with `System.getProperty`.

## 3. Core concept

```bash
# Run with arguments
java MyApp arg0 arg1 "arg with spaces"

# With -cp (classpath) and system properties: flags BEFORE class name
java -cp . -Denv=prod MyApp --port 8080

# The JVM collects only tokens AFTER the class name:
#   args = {"--port", "8080"}
# -cp and -D flags are JVM flags, NOT in args

# In code:
public static void main(String[] args) {
    System.out.println(args.length);   // number of arguments
    System.out.println(args[0]);       // first argument (or ArrayIndexOutOfBoundsException if none)

    // Safe access
    if (args.length > 0) System.out.println(args[0]);

    // Parse typed values
    int port = Integer.parseInt(args[1]);
    double amount = Double.parseDouble(args[2]);

    // Common pattern: --key value pairs
    Map<String, String> opts = parseOpts(args);
}
```

Key facts:
- `args` is never `null` — an empty launch has `args.length == 0`.
- Every element is a `String` — convert to `int`/`double`/etc. with `Integer.parseInt`, `Double.parseDouble`.
- Spaces inside quotes (`"hello world"`) become a single element on most shells.
- JVM flags (`-Xmx512m`, `-cp`, `-D...`) come before the class name — they are NOT in `args`.

## 4. Diagram

<svg viewBox="0 0 700 185" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Command-line tokens split into JVM flags and program arguments passed as String array">
  <rect x="8" y="8" width="684" height="169" rx="8" fill="#0d1117"/>

  <!-- Command line -->
  <rect x="20" y="20" width="655" height="30" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="35" y="40" fill="#8b949e" font-size="9" font-family="monospace">$ java  -Xmx512m  -Denv=prod  MyApp  --port  8080  --name  "Alice"</text>

  <!-- Labels below command -->
  <text x="40"  y="65" fill="#79c0ff" font-size="8" font-family="sans-serif">launcher</text>
  <text x="90"  y="65" fill="#8b949e" font-size="8" font-family="sans-serif">JVM flag</text>
  <text x="182" y="65" fill="#8b949e" font-size="8" font-family="sans-serif">system prop</text>
  <text x="302" y="65" fill="#6db33f" font-size="8" font-family="sans-serif">class name</text>
  <text x="368" y="65" fill="#e6edf3" font-size="8" font-family="sans-serif">args[0]</text>
  <text x="417" y="65" fill="#e6edf3" font-size="8" font-family="sans-serif">args[1]</text>
  <text x="462" y="65" fill="#e6edf3" font-size="8" font-family="sans-serif">args[2]</text>
  <text x="519" y="65" fill="#e6edf3" font-size="8" font-family="sans-serif">args[3]</text>

  <!-- String[] args box -->
  <rect x="338" y="80" width="345" height="80" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="510" y="97" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">String[] args</text>
  <text x="358" y="113" fill="#e6edf3" font-size="9" font-family="monospace">args[0] = "--port"</text>
  <text x="358" y="127" fill="#e6edf3" font-size="9" font-family="monospace">args[1] = "8080"</text>
  <text x="358" y="141" fill="#e6edf3" font-size="9" font-family="monospace">args[2] = "--name"</text>
  <text x="358" y="155" fill="#e6edf3" font-size="9" font-family="monospace">args[3] = "Alice"</text>

  <!-- System.getProperty -->
  <rect x="20" y="80" width="240" height="45" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="130" y="98" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">System.getProperty("env")</text>
  <text x="130" y="115" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">returns "prod" (from -Denv=prod)</text>

  <rect x="20" y="132" width="240" height="28" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="130" y="150" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">-Xmx512m → heap limit (JVM internal)</text>
</svg>

JVM flags (before the class name) go to the JVM; everything after the class name goes into `String[] args`. System properties (`-D`) are readable via `System.getProperty()`.

## 5. Runnable example

Scenario: a file-conversion utility that takes source and destination paths as arguments, with optional flags for format and verbosity — progressing from raw arg access to structured parsing to a production-ready tool.

### Level 1 — Basic

```java
// ArgsBasic.java — read and display raw command-line arguments
public class ArgsBasic {
    public static void main(String[] args) {
        System.out.println("=== Command-line arguments demo ===\n");
        System.out.println("args.length = " + args.length);

        if (args.length == 0) {
            System.out.println("No arguments provided.");
            System.out.println("Try: java ArgsBasic.java hello world 42");
            return;
        }

        for (int i = 0; i < args.length; i++) {
            System.out.printf("args[%d] = \"%s\" (type: String)%n", i, args[i]);
        }

        // Safe first-arg access
        System.out.println("\nFirst arg: " + args[0]);

        // Type conversion (will throw NumberFormatException if not a number)
        System.out.println("\nTrying to parse each arg as number:");
        for (String arg : args) {
            try {
                long n = Long.parseLong(arg);
                System.out.println("  \"" + arg + "\" → long " + n);
            } catch (NumberFormatException e) {
                System.out.println("  \"" + arg + "\" → not a number");
            }
        }
    }
}
```

**How to run:** `java ArgsBasic.java hello world 42 3.14`

Expected output:
```
=== Command-line arguments demo ===

args.length = 4
args[0] = "hello" (type: String)
args[1] = "world" (type: String)
args[2] = "42" (type: String)
args[3] = "3.14" (type: String)

First arg: hello

Trying to parse each arg as number:
  "hello" → not a number
  "world" → not a number
  "42" → long 42
  "3.14" → not a number
```

Every command-line argument arrives as a `String` — even `42`. Always parse numeric arguments explicitly. A missing argument causes `ArrayIndexOutOfBoundsException` if you access `args[i]` without checking `args.length > i`.

### Level 2 — Intermediate

Same file-conversion scenario: parse `--key value` flag pairs, validate required arguments, and report a clear error when something is missing.

```java
// ArgsConverter.java — file conversion tool with structured arg parsing
import java.util.*;

public class ArgsConverter {

    public static void main(String[] args) {
        if (args.length == 0 || Arrays.asList(args).contains("--help")) {
            System.out.println("Usage: java ArgsConverter.java <source> <dest> [--format csv|json|tsv] [--verbose]");
            System.out.println("  source   path to input file");
            System.out.println("  dest     path to output file");
            System.out.println("  --format output format (default: csv)");
            System.out.println("  --verbose print progress");
            return;
        }

        // Positional args: first two non-flag tokens are source and dest
        List<String> positional = new ArrayList<>();
        Map<String, String> flags = new LinkedHashMap<>();

        for (int i = 0; i < args.length; i++) {
            if (args[i].startsWith("--")) {
                String key = args[i].substring(2);
                if (i + 1 < args.length && !args[i + 1].startsWith("--")) {
                    flags.put(key, args[++i]);
                } else {
                    flags.put(key, "true");
                }
            } else {
                positional.add(args[i]);
            }
        }

        if (positional.size() < 2) {
            System.err.println("Error: source and dest paths are required.");
            System.exit(1);
        }

        String source  = positional.get(0);
        String dest    = positional.get(1);
        String format  = flags.getOrDefault("format", "csv");
        boolean verbose = flags.containsKey("verbose");

        if (!Set.of("csv", "json", "tsv").contains(format)) {
            System.err.println("Error: --format must be csv, json, or tsv. Got: " + format);
            System.exit(1);
        }

        System.out.println("=== File Converter ===");
        System.out.println("Source:  " + source);
        System.out.println("Dest:    " + dest);
        System.out.println("Format:  " + format);
        System.out.println("Verbose: " + verbose);

        if (verbose) {
            System.out.println("\n[VERBOSE] Reading from: " + source);
            System.out.println("[VERBOSE] Converting to: " + format.toUpperCase());
            System.out.println("[VERBOSE] Writing to:   " + dest);
        }

        System.out.println("\nConversion complete: " + source + " → " + dest + " (" + format + ")");
    }
}
```

**How to run:** `java ArgsConverter.java input.csv output.json --format json --verbose`

Expected output:
```
=== File Converter ===
Source:  input.csv
Dest:    output.json
Format:  json
Verbose: true

[VERBOSE] Reading from: input.csv
[VERBOSE] Converting to: JSON
[VERBOSE] Writing to:   output.json

Conversion complete: input.csv → output.json (json)
```

Positional arguments (source, dest) and named flags (`--format json`) require different parsing logic. This pattern separates the two clearly: collect positionals and flags in one loop, then validate afterward.

### Level 3 — Advanced

Same converter grown to support multiple input files, `--` to stop flag parsing, environment-variable defaults, and a full usage error report listing every problem found.

```java
// ArgsAdvanced.java — production-quality arg parsing with multi-file support
import java.util.*;
import java.util.stream.*;

public class ArgsAdvanced {

    record ConvertJob(List<String> sources, String dest, String format,
                      boolean verbose, int threads) {}

    public static void main(String[] args) {
        if (args.length == 0 || contains(args, "--help", "-h")) {
            printHelp(); return;
        }

        List<String> errors = new ArrayList<>();
        ConvertJob job = parse(args, errors);

        if (!errors.isEmpty()) {
            System.err.println("Argument errors:");
            errors.forEach(e -> System.err.println("  • " + e));
            System.err.println("\nRun with --help for usage.");
            System.exit(2);
        }

        System.out.println("=== Batch File Converter ===");
        System.out.println("Sources:  " + job.sources());
        System.out.println("Dest dir: " + job.dest());
        System.out.println("Format:   " + job.format());
        System.out.println("Threads:  " + job.threads());

        // Simulate batch conversion
        for (String source : job.sources()) {
            String outFile = job.dest() + "/" + source.replaceAll("\\.[^.]+$", "." + job.format());
            if (job.verbose()) System.out.println("  Converting: " + source + " → " + outFile);
            // real conversion would go here
        }
        System.out.println("\nAll done. " + job.sources().size() + " file(s) converted.");
    }

    static ConvertJob parse(String[] args, List<String> errors) {
        List<String> sources = new ArrayList<>();
        Map<String, String> flags = new LinkedHashMap<>();
        boolean pastDoubleDash = false;

        for (int i = 0; i < args.length; i++) {
            if ("--".equals(args[i])) { pastDoubleDash = true; continue; }
            if (!pastDoubleDash && args[i].startsWith("--")) {
                String key = args[i].substring(2);
                if (i + 1 < args.length && !args[i + 1].startsWith("--")) {
                    flags.put(key, args[++i]);
                } else {
                    flags.put(key, "true");
                }
            } else {
                sources.add(args[i]);
            }
        }

        // dest: arg > env var
        String dest = flags.get("output");
        if (dest == null) dest = System.getenv("CONVERT_OUTPUT_DIR");
        if (dest == null || dest.isBlank()) errors.add("--output <dir> is required (or set CONVERT_OUTPUT_DIR)");

        // format: arg > env var > default
        String format = flags.getOrDefault("format",
            Optional.ofNullable(System.getenv("CONVERT_FORMAT")).orElse("csv"));
        if (!Set.of("csv", "json", "tsv", "parquet").contains(format))
            errors.add("--format must be csv|json|tsv|parquet, got: " + format);

        // threads
        String threadStr = flags.getOrDefault("threads", "1");
        int threads = 1;
        try {
            threads = Integer.parseInt(threadStr);
            if (threads < 1 || threads > 64) errors.add("--threads must be 1–64, got: " + threadStr);
        } catch (NumberFormatException e) {
            errors.add("--threads must be an integer, got: " + threadStr);
        }

        if (sources.isEmpty()) errors.add("At least one source file is required");

        boolean verbose = flags.containsKey("verbose");
        return new ConvertJob(sources, dest != null ? dest : "", format, verbose, threads);
    }

    static void printHelp() {
        System.out.println("""
            Usage: java ArgsAdvanced.java <file1> [file2 ...] --output <dir> [options]

            Required:
              --output <dir>         output directory (or CONVERT_OUTPUT_DIR env var)

            Options:
              --format csv|json|tsv|parquet  output format (default: csv, or CONVERT_FORMAT env var)
              --threads <n>           parallel workers 1-64 (default: 1)
              --verbose               print per-file progress
              --                      stop flag parsing (remaining args are files)
              -h, --help              show this help

            Examples:
              java ArgsAdvanced.java data.csv log.csv --output ./out --format json
              CONVERT_OUTPUT_DIR=./out java ArgsAdvanced.java *.csv
            """);
    }

    static boolean contains(String[] arr, String... vals) {
        Set<String> set = Set.of(vals);
        for (String a : arr) if (set.contains(a)) return true;
        return false;
    }
}
```

**How to run:** `java ArgsAdvanced.java a.csv b.csv --output /tmp/out --format json --threads 4 --verbose`

The `--` sentinel stops flag parsing — anything after `--` is treated as a positional (source file), even if it starts with `--`. `errors` is a list rather than an early exit, so all problems are reported at once rather than one-at-a-time.

## 6. Walkthrough

Execution trace in `ArgsAdvanced.main` for:
`java ArgsAdvanced.java a.csv b.csv --output /tmp/out --format json --threads 4 --verbose`

**`main` entry.** `args = {"a.csv","b.csv","--output","/tmp/out","--format","json","--threads","4","--verbose"}`. Not empty, doesn't contain `--help`.

**`parse` loop.** Iterates:
- `"a.csv"` — no `--` prefix → `sources.add("a.csv")`
- `"b.csv"` → `sources.add("b.csv")`
- `"--output"` → key="output", next="``/tmp/out`" (not starting `--`) → `flags.put("output","/tmp/out")`, i advances past `/tmp/out`
- `"--format"` → key="format", next="json" → `flags.put("format","json")`, i advances
- `"--threads"` → key="threads", next="4" → `flags.put("threads","4")`, i advances
- `"--verbose"` → key="verbose", next is out of bounds → `flags.put("verbose","true")`

**Validation.** `dest="/tmp/out"` (from flag). `format="json"` — in allowed set. `threads=4` — `Integer.parseInt("4")` = 4, range 1–64 OK. `sources=["a.csv","b.csv"]` — not empty. `errors` is empty.

**Back in `main`.** `errors.isEmpty()` → true, proceed. Prints config. For each source: `outFile = "/tmp/out/" + "a" + ".json"`. Verbose → prints conversion line.

**Request/response analogy.** The shell sends the argument tokens as the "request". `parse` processes them and returns a typed `ConvertJob` as the "response". If the request is malformed, `errors` accumulates problems and the tool exits with code 2 (argument misuse) after showing all errors at once.

## 7. Gotchas & takeaways

> **`args.length == 0` does not crash — `args[0]` does.** `args` is never `null`, but accessing `args[0]` when `args.length == 0` throws `ArrayIndexOutOfBoundsException`. Always guard positional access with a length check.

> **JVM flags vs. program args.** `-Xmx512m`, `-cp`, `-jar`, and `-D...` come before the class/jar name and are NOT part of `args`. If you run `java -Dprop=val MyApp --flag`, then `args = {"--flag"}` and `System.getProperty("prop")` returns `"val"`.

- `args.length` — always check before accessing by index.
- `Integer.parseInt(args[i])` — wrap in `try-catch NumberFormatException` at system boundaries.
- `Arrays.asList(args).contains("--help")` — simplest check for a flag anywhere in the array.
- Spaces in args: `"hello world"` is one element on most shells; `hello world` is two.
- For complex CLI tools, use Apache Commons CLI or picocli rather than hand-rolling parsers.
