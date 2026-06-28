---
card: spring-boot
gi: 100
slug: color-coded-output
title: Color-coded output
---

## 1. What it is

Spring Boot's console output uses **ANSI escape codes** to colour log lines by level, making it easier to visually scan output in a terminal:

| Level | Default colour |
|---|---|
| `ERROR` | Red (bold) |
| `WARN` | Yellow |
| `INFO` | Green |
| `DEBUG` | Green |
| `TRACE` | Green |

Colour is also applied to the timestamp (faint), the PID (magenta), and the logger name (cyan in some versions). The `---` separator and thread name are uncoloured.

Colour support is controlled by `spring.output.ansi.enabled`:
- `DETECT` (default) — enables colour if the output is a terminal that reports ANSI support.
- `ALWAYS` — forces colour regardless of terminal detection.
- `NEVER` — disables colour entirely.

## 2. Why & when

In a busy log stream, colour lets your eye jump directly to `ERROR` (red) or `WARN` (yellow) without reading every line. Without colour, `INFO` and `ERROR` look identical at a glance.

Colour is:
- **Useful in local development** — real terminal, interactive debugging.
- **Counterproductive in CI/CD logs** — the ANSI escape codes (`[31m`) appear as literal garbled characters in systems that don't interpret ANSI (Jenkins, some log aggregators).
- **Irrelevant in production** — logs are typically piped to a file or log aggregator; colour is stripped or clutters the storage.

Spring Boot's `DETECT` mode automatically disables colour when stdout is not a TTY — so it works correctly by default in both environments. You need to override it only when the detection gives the wrong result (e.g. a CI system that supports ANSI but incorrectly reports non-TTY).

## 3. Core concept

Spring Boot uses Logback's `%clr(…){}` conversion specifier (provided by `AnsiOutput` and `ExtendedWhitespaceThrowableProxyConverter`):

```
%clr(%d{…}){faint}        → timestamp in faint/dim colour
%clr(${PID}){magenta}     → PID in magenta
%clr(%-5level){level}     → log level with its level-specific colour
%clr(${LOG_EXCEPTION_CONVERSION_WORD}){red}  → stack traces in red
```

The `{level}` colour keyword tells Logback to use the level-to-colour mapping table; `{faint}`, `{magenta}`, `{red}`, `{green}`, `{cyan}`, `{blue}`, `{yellow}` are fixed colours.

You can use these in custom patterns:
```properties
logging.pattern.console=%clr(%d{HH:mm:ss.SSS}){faint} %clr(%-5level){level} %clr(%logger{36}){cyan} - %msg%n
```

`AnsiOutput.setEnabled(AnsiOutput.Enabled.ALWAYS)` can also be called programmatically.

## 4. Diagram

<svg viewBox="0 0 680 230" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Console log lines with colour coding: ERROR in red, WARN in yellow, INFO in green, all other fields coloured appropriately">
  <rect x="8" y="8" width="664" height="214" rx="12" fill="#0d1117" stroke="#30363d" stroke-width="1"/>
  <text x="340" y="30" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="sans-serif" font-weight="bold">ANSI-Coloured Console Output</text>

  <!-- Log lines -->
  <text x="26" y="56" fill="#8b949e" font-size="10" font-family="monospace">2026-06-28T10:15:30.123Z</text>
  <text x="208" y="56" fill="#6db33f" font-size="10" font-family="monospace" font-weight="bold"> INFO</text>
  <text x="246" y="56" fill="#e6edf3" font-size="10" font-family="monospace"> 12345 ---</text>
  <text x="324" y="56" fill="#79c0ff" font-size="10" font-family="monospace"> [main]</text>
  <text x="374" y="56" fill="#8b949e" font-size="10" font-family="monospace"> c.e.demo.AppStartup       :</text>
  <text x="520" y="56" fill="#e6edf3" font-size="10" font-family="monospace"> Application started</text>

  <text x="26" y="76" fill="#8b949e" font-size="10" font-family="monospace">2026-06-28T10:15:31.456Z</text>
  <text x="208" y="76" fill="#e3b341" font-size="10" font-family="monospace" font-weight="bold"> WARN</text>
  <text x="246" y="76" fill="#e6edf3" font-size="10" font-family="monospace"> 12345 ---</text>
  <text x="324" y="76" fill="#79c0ff" font-size="10" font-family="monospace"> [main]</text>
  <text x="374" y="76" fill="#8b949e" font-size="10" font-family="monospace"> c.e.demo.CacheService     :</text>
  <text x="520" y="76" fill="#e6edf3" font-size="10" font-family="monospace"> Cache miss rate 45%</text>

  <text x="26" y="96" fill="#8b949e" font-size="10" font-family="monospace">2026-06-28T10:15:31.789Z</text>
  <text x="208" y="96" fill="#f85149" font-size="10" font-family="monospace" font-weight="bold"> ERROR</text>
  <text x="248" y="96" fill="#e6edf3" font-size="10" font-family="monospace"> 12345 ---</text>
  <text x="326" y="96" fill="#79c0ff" font-size="10" font-family="monospace"> [main]</text>
  <text x="376" y="96" fill="#8b949e" font-size="10" font-family="monospace"> c.e.demo.PaymentService   :</text>
  <text x="520" y="96" fill="#e6edf3" font-size="10" font-family="monospace"> DB timeout - retry 1/3</text>

  <text x="26" y="116" fill="#8b949e" font-size="10" font-family="monospace">2026-06-28T10:15:32.000Z</text>
  <text x="208" y="116" fill="#6db33f" font-size="10" font-family="monospace"> DEBUG</text>
  <text x="250" y="116" fill="#e6edf3" font-size="10" font-family="monospace"> 12345 ---</text>
  <text x="328" y="116" fill="#79c0ff" font-size="10" font-family="monospace"> [main]</text>
  <text x="378" y="116" fill="#8b949e" font-size="10" font-family="monospace"> c.e.demo.RetryPolicy      :</text>
  <text x="520" y="116" fill="#e6edf3" font-size="10" font-family="monospace"> Backoff 500ms then retry</text>

  <!-- Colour legend -->
  <rect x="26" y="138" width="620" height="64" rx="6" fill="#161b22" stroke="#30363d" stroke-width="1"/>
  <text x="340" y="155" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">Colour map (ANSI codes in Logback %clr conversion)</text>
  <text x="80"  y="172" fill="#f85149" font-size="10" font-family="monospace">ERROR → red</text>
  <text x="220" y="172" fill="#e3b341" font-size="10" font-family="monospace">WARN → yellow</text>
  <text x="360" y="172" fill="#6db33f" font-size="10" font-family="monospace">INFO → green</text>
  <text x="500" y="172" fill="#6db33f" font-size="10" font-family="monospace">DEBUG → green</text>
  <text x="80"  y="190" fill="#8b949e" font-size="10" font-family="monospace">timestamp → faint</text>
  <text x="280" y="190" fill="#bc8cff" font-size="10" font-family="monospace">PID → magenta</text>
  <text x="460" y="190" fill="#8b949e" font-size="10" font-family="monospace">loggerName → cyan</text>
</svg>

Colour is applied per-field by Logback's `%clr` conversion; `DETECT` mode enables it only when stdout is a TTY.

## 5. Runnable example

```java
// ColorOutput.java — run: java ColorOutput.java  (JDK 17+)
// Demonstrates ANSI colour codes as used by Spring Boot's Logback pattern.

public class ColorOutput {

    // ANSI escape sequences
    static final String RESET   = "[0m";
    static final String BOLD    = "[1m";
    static final String FAINT   = "[2m";
    static final String RED     = "[31m";
    static final String GREEN   = "[32m";
    static final String YELLOW  = "[33m";
    static final String MAGENTA = "[35m";
    static final String CYAN    = "[36m";

    static String colourLevel(String level) {
        return switch (level) {
            case "ERROR" -> BOLD + RED    + level + RESET;
            case "WARN"  ->        YELLOW + level + RESET;
            default      ->        GREEN  + level + RESET;  // INFO, DEBUG, TRACE
        };
    }

    static void log(String level, String logger, String message) {
        String ts     = FAINT + "2026-06-28T10:15:30.123Z" + RESET;
        String lvl    = String.format("%-5s", colourLevel(level));
        String pid    = MAGENTA + "12345" + RESET;
        String thread = "[" + Thread.currentThread().getName() + "]";
        String log    = CYAN + String.format("%-35s", logger) + RESET;
        System.out.printf("%s %s %s --- %-15s %s : %s%n",
                ts, lvl, pid, thread, log, message);
    }

    static boolean isAnsiSupported() {
        // Mirrors Spring Boot's DETECT logic: check if stdout is a real terminal
        // In practice: System.console() != null || TERM env var is set
        String term = System.getenv("TERM");
        boolean hasConsole = System.console() != null;
        return hasConsole || (term != null && !term.equals("dumb"));
    }

    public static void main(String[] args) {
        System.out.println("ANSI supported (DETECT): " + isAnsiSupported());
        System.out.println("Control via: spring.output.ansi.enabled=DETECT|ALWAYS|NEVER");
        System.out.println();

        log("INFO",  "com.example.demo.AppStartup",    "Application started on port 8080");
        log("DEBUG", "com.example.demo.OrderService",  "Entering processOrder(orderId=42)");
        log("INFO",  "com.example.demo.OrderService",  "Order 42 processed in 52ms");
        log("WARN",  "com.example.demo.CacheService",  "Cache miss rate 45% — consider warming");
        log("ERROR", "com.example.demo.PaymentService","DB timeout — retry 1/3");
        log("INFO",  "com.example.demo.AppShutdown",   "Application shutting down");

        System.out.println();
        System.out.println("Custom pattern property example:");
        System.out.println("  logging.pattern.console="
                + "%clr(%d{HH:mm:ss.SSS}){faint} %clr(%-5level){level} "
                + "%clr(%logger{36}){cyan} - %msg%n");
    }
}
```

**How to run:** `java ColorOutput.java`

Run in a standard terminal to see colour. Pipe to a file (`java ColorOutput.java > out.txt`) to see the raw ANSI codes as plain text — demonstrating why CI systems need `spring.output.ansi.enabled=NEVER`.

## 6. Walkthrough

- `"[31m"` is the ANSI CSI sequence for red foreground. `"[0m"` resets all attributes. `"[1m"` is bold. These are the same bytes Logback's `AnsiElement` emits.
- `colourLevel(level)` maps the level string to its ANSI colour. `ERROR` gets bold red for maximum visibility; `WARN` gets yellow; everything else gets green. This mirrors `AnsiColor` values in `org.springframework.boot.ansi`.
- `FAINT + timestamp + RESET` — the timestamp is rendered in dim grey, visually receding so that the level and message stand out. You can see this effect clearly in a real terminal.
- `isAnsiSupported()` — Spring Boot's `DETECT` mode calls `AnsiOutput.isTerminal()` which checks `System.console() != null` (null when stdout is redirected) and the `TERM` environment variable (absent or `"dumb"` in non-colour environments).
- Running with `> out.txt` writes `[31mERROR[0m` literally to the file — showing why log files and log aggregators should use `NEVER`.

## 7. Gotchas & takeaways

> **Log aggregators (ELK, Splunk, Datadog) index raw bytes.** ANSI codes become literal `[31m` sequences in the stored log, cluttering searches and making regex-based parsing fragile. Always use `spring.output.ansi.enabled=NEVER` when stdout is captured by a log shipper.

> **Some CI systems support ANSI but Spring Boot detects `NEVER` because they redirect stdout.** For Jenkins with the AnsiColor plugin, set `spring.output.ansi.enabled=ALWAYS` in the test `application.properties` or as a JVM arg. For GitHub Actions (which supports ANSI in workflow logs), the default `DETECT` usually works because `System.console()` is non-null.

- `spring.output.ansi.enabled=DETECT` is correct for 95% of cases — leave it at the default.
- Colour is a developer convenience; it carries no information not already present in the log level string. Never rely on colour for log parsing.
- You can use `%clr(…){colour}` in custom `logging.pattern.console` values to apply arbitrary colours to any field.
- `AnsiOutput.setEnabled(AnsiOutput.Enabled.ALWAYS)` in `main()` or a test `@BeforeAll` provides programmatic control for testing.
- The Spring Boot banner at startup also uses ANSI colour — it respects the same `spring.output.ansi.enabled` setting.
