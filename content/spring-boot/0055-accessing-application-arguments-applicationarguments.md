---
card: spring-boot
gi: 55
slug: accessing-application-arguments-applicationarguments
title: Accessing application arguments (ApplicationArguments)
---

## 1. What it is

**`ApplicationArguments`** is a Spring Boot interface that provides access to the command-line arguments passed to `SpringApplication.run()`. It parses them into two categories:

- **Option arguments** — arguments starting with `--`, e.g. `--debug=true` or `--spring.profiles.active=prod`. These are key-value pairs.
- **Non-option arguments** — positional arguments without `--`, e.g. `input.csv` or `process`.

Spring Boot auto-registers an `ApplicationArguments` bean, so any Spring component can inject it:

```java
@Component
public class MyBean {
    public MyBean(ApplicationArguments args) {
        List<String> files = args.getNonOptionArgs();       // positional args
        boolean debug = args.containsOption("debug");       // --debug flag
        List<String> profiles = args.getOptionValues("spring.profiles.active");
    }
}
```

The raw `String[]` is also available via `@Value("#{systemProperties['sun.java.command']}")` but `ApplicationArguments` is the structured, Spring-idiomatic way.

## 2. Why & when

Command-line arguments are the standard way to pass runtime configuration to a JVM application: input file paths, operation modes, feature flags. `ApplicationArguments` parses them consistently so you don't need to write your own argument parser.

Use `ApplicationArguments` when:
- Writing batch jobs or CLI tools where the user specifies input files or parameters at startup.
- Dynamically enabling features based on startup flags (`--export`, `--dry-run`).
- Writing a Spring Boot application that doubles as both a web service and a CLI tool depending on the arguments.

For environment configuration (DB URLs, API keys), prefer `application.properties` or environment variables over command-line arguments — command-line args are visible in `ps` output.

## 3. Core concept

When `SpringApplication.run(MyApp.class, args)` is called, Spring Boot:
1. Passes `args` to `DefaultApplicationArguments(args)`, which parses them using SimpleCommandLinePropertySource logic.
2. Registers the resulting `ApplicationArguments` object as a singleton bean named `springApplicationArguments`.
3. Also adds the option arguments as a property source, so `--server.port=9090` overrides `application.properties`.

Parsing rules:
- `--key=value` → option argument with key "key" and value "value".
- `--key` (no value) → option argument with key "key" and empty value list; `containsOption("key")` returns `true`.
- `value` (no `--`) → non-option argument; added to `getNonOptionArgs()`.
- Multiple values for one key: `--profiles=dev --profiles=test` → `getOptionValues("profiles")` returns `["dev", "test"]`.

## 4. Diagram

<svg viewBox="0 0 660 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="ApplicationArguments parsing command-line args into option and non-option categories">
  <!-- Raw args -->
  <rect x="20" y="20" width="340" height="50" rx="6" fill="#2d3748" stroke="#8b949e" stroke-width="1.5"/>
  <text x="30" y="42" fill="#e6edf3" font-size="11" font-family="monospace">$ java -jar app.jar --debug --profiles=dev input.csv</text>
  <text x="30" y="60" fill="#8b949e" font-size="10" font-family="monospace">args[] passed to SpringApplication.run()</text>

  <!-- Parser -->
  <rect x="200" y="90" width="260" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="330" y="115" fill="#6db33f" font-size="11" font-family="monospace" text-anchor="middle">DefaultApplicationArguments(args)</text>

  <!-- Option args -->
  <rect x="20" y="150" width="280" height="56" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="160" y="172" fill="#79c0ff" font-size="11" font-family="monospace" text-anchor="middle">Option arguments</text>
  <text x="36" y="192" fill="#8b949e" font-size="10" font-family="monospace">containsOption("debug") → true</text>
  <text x="36" y="206" fill="#8b949e" font-size="10" font-family="monospace">getOptionValues("profiles") → [dev]</text>

  <!-- Non-option args -->
  <rect x="360" y="150" width="280" height="56" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="500" y="172" fill="#8b949e" font-size="11" font-family="monospace" text-anchor="middle">Non-option arguments</text>
  <text x="376" y="192" fill="#8b949e" font-size="10" font-family="monospace">getNonOptionArgs() → [input.csv]</text>

  <!-- Arrows -->
  <line x1="190" y1="50" x2="280" y2="88" stroke="#8b949e" stroke-width="1.5" stroke-dasharray="4,3" marker-end="url(#aa)"/>
  <line x1="280" y1="130" x2="160" y2="148" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#aa)"/>
  <line x1="380" y1="130" x2="500" y2="148" stroke="#8b949e" stroke-width="1.5" marker-end="url(#aa)"/>

  <defs>
    <marker id="aa" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/>
    </marker>
  </defs>
</svg>

`DefaultApplicationArguments` splits `args[]` into option arguments (`--key=value`) and non-option arguments (positional values).

## 5. Runnable example

```java
// ApplicationArgumentsDemo.java
// How to run: java ApplicationArgumentsDemo.java --debug --profiles=dev --profiles=prod input.csv report.csv
// (JDK 17+) — demonstrates ApplicationArguments parsing without Spring.

import java.util.*;

public class ApplicationArgumentsDemo {

    // ── Simulated ApplicationArguments ────────────────────────────
    static class ApplicationArguments {
        private final Map<String, List<String>> options = new LinkedHashMap<>();
        private final List<String> nonOptions = new ArrayList<>();
        private final List<String> rawArgs;

        ApplicationArguments(String[] args) {
            this.rawArgs = Arrays.asList(args);
            for (String arg : args) {
                if (arg.startsWith("--")) {
                    String stripped = arg.substring(2);
                    int eq = stripped.indexOf('=');
                    if (eq >= 0) {
                        String key = stripped.substring(0, eq);
                        String val = stripped.substring(eq + 1);
                        options.computeIfAbsent(key, k -> new ArrayList<>()).add(val);
                    } else {
                        options.computeIfAbsent(stripped, k -> new ArrayList<>());
                    }
                } else {
                    nonOptions.add(arg);
                }
            }
        }

        List<String> getSourceArgs()                    { return rawArgs; }
        Set<String>  getOptionNames()                   { return options.keySet(); }
        boolean      containsOption(String name)        { return options.containsKey(name); }
        List<String> getOptionValues(String name)       { return options.getOrDefault(name, List.of()); }
        List<String> getNonOptionArgs()                 { return nonOptions; }
    }

    public static void main(String[] args) {
        // Simulate: java -jar app.jar --debug --profiles=dev --profiles=prod input.csv report.csv
        if (args.length == 0) {
            args = new String[]{"--debug", "--profiles=dev", "--profiles=prod", "input.csv", "report.csv"};
        }

        ApplicationArguments appArgs = new ApplicationArguments(args);

        System.out.println("=== ApplicationArguments demo ===\n");
        System.out.println("Raw args:       " + appArgs.getSourceArgs());
        System.out.println("Option names:   " + appArgs.getOptionNames());
        System.out.println();

        System.out.println("containsOption(\"debug\")    → " + appArgs.containsOption("debug"));
        System.out.println("containsOption(\"verbose\")  → " + appArgs.containsOption("verbose"));
        System.out.println("getOptionValues(\"profiles\") → " + appArgs.getOptionValues("profiles"));
        System.out.println("getNonOptionArgs()          → " + appArgs.getNonOptionArgs());

        System.out.println("\n--- Practical use: batch job ---");
        if (appArgs.containsOption("debug")) {
            System.out.println("DEBUG mode enabled");
        }
        List<String> profiles = appArgs.getOptionValues("profiles");
        if (!profiles.isEmpty()) {
            System.out.println("Active profiles: " + profiles);
        }
        List<String> inputFiles = appArgs.getNonOptionArgs();
        if (inputFiles.isEmpty()) {
            System.out.println("No input files provided.");
        } else {
            inputFiles.forEach(f -> System.out.println("Processing file: " + f));
        }
    }
}
```

**How to run:** `java ApplicationArgumentsDemo.java --debug --profiles=dev --profiles=prod input.csv report.csv`

Expected output:
```
=== ApplicationArguments demo ===

Raw args:       [--debug, --profiles=dev, --profiles=prod, input.csv, report.csv]
Option names:   [debug, profiles]

containsOption("debug")    → true
containsOption("verbose")  → false
getOptionValues("profiles") → [dev, prod]
getNonOptionArgs()          → [input.csv, report.csv]

--- Practical use: batch job ---
DEBUG mode enabled
Active profiles: [dev, prod]
Processing file: input.csv
Processing file: report.csv
```

## 6. Walkthrough

- The `ApplicationArguments` constructor loops through `args[]`. Each `--key=value` arg is split on `=` and stored in `options`. A `--flag` with no `=` stores an empty list under the flag name. Everything else goes to `nonOptions`.
- `containsOption("debug")` returns `true` because `--debug` populated an empty list entry for "debug".
- `getOptionValues("profiles")` returns `["dev", "prod"]` because two separate `--profiles=X` args were processed — multi-value keys are fully supported.
- `getNonOptionArgs()` collects `["input.csv", "report.csv"]` — the positional arguments the batch job will process.
- The "Practical use" section shows the pattern: check option flags, read option values, iterate non-option args.

## 7. Gotchas & takeaways

> Option arguments (`--key=value`) passed on the command line are added to the Spring `Environment` as a property source with **high priority**, overriding `application.properties`. This means `--server.port=9090` on the command line changes the server port, even if `application.properties` says `server.port=8080`.

> `containsOption("key")` returns `true` for `--key` (no value) even though `getOptionValues("key")` returns an empty list. This is the correct way to detect boolean flags — check `containsOption`, not `getOptionValues().isEmpty()`.

- Inject `ApplicationArguments` in any `@Component` via constructor or `@Autowired` — Spring auto-registers it as a singleton.
- `getSourceArgs()` returns the original `String[]` as-is, useful for logging startup configuration.
- In tests, use `@SpringBootTest(args = "--debug --profiles=test")` to simulate command-line args.
- For complex argument parsing (subcommands, validation, help text), consider Spring Shell or Picocli — `ApplicationArguments` handles simple flags and files well but is not a full CLI framework.
