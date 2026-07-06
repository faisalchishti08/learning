---
card: java
gi: 344
slug: java-util-logging-logger-level-handler
title: java.util.logging (Logger, Level, Handler)
---

## 1. What it is

`java.util.logging` (often called JUL) is the JDK's built-in logging framework, built around three core pieces: a `Logger` (the object your code calls to emit log messages, usually one per class), a `Level` (a severity ranking — `SEVERE`, `WARNING`, `INFO`, `CONFIG`, `FINE`, `FINER`, `FINEST` — that determines whether a given message is important enough to actually be recorded), and a `Handler` (the destination a log record is sent to, such as the console or a file). A logger only emits a message if its effective level permits it, and a handler only outputs a message if the handler's own level also permits it — both gates must pass.

```java
import java.util.logging.Logger;
import java.util.logging.Level;

public class LoggingDemo {
    private static final Logger logger = Logger.getLogger(LoggingDemo.class.getName());

    public static void main(String[] args) {
        logger.info("Application starting");
        logger.warning("Low disk space detected");
        logger.log(Level.SEVERE, "Failed to connect to database");
    }
}
```

`Logger.getLogger(name)` retrieves (or creates) a named logger — by convention using the fully-qualified class name — and calling `.info()`, `.warning()`, or `.log(level, message)` records a message at that specific severity level.

## 2. Why & when

`System.out.println` gives no way to filter by severity, redirect output to a file, or turn verbosity up and down without changing code — a real logging framework solves all three, letting operators control what gets recorded (and where) without touching the application's source.

- **Recording application events at appropriate severity** — routine operational messages at `INFO`, recoverable problems at `WARNING`, and genuine failures at `SEVERE`, so log readers (human or automated) can filter by importance.
- **Controlling verbosity without code changes** — adjusting a logger's level (or a handler's level) via configuration lets you get detailed `FINE`-level tracing in a debugging session without recompiling, then dial it back down in production.
- **Routing output to different destinations** — a `ConsoleHandler` for immediate visibility during development, a `FileHandler` for persistent records, or a custom handler forwarding to a centralized logging system.

`java.util.logging` is the JDK's built-in option and requires no external dependency, but many real-world Java projects use a different logging facade (like SLF4J) paired with a more feature-rich backend (like Logback or Log4j2) — understanding JUL's model (loggers, levels, handlers) still transfers directly, since most alternatives follow the same basic structure.

## 3. Core concept

```java
import java.util.logging.*;

public class LoggingCore {
    private static final Logger logger = Logger.getLogger(LoggingCore.class.getName());

    public static void main(String[] args) {
        logger.setLevel(Level.FINE); // logger itself allows FINE and above

        ConsoleHandler handler = new ConsoleHandler();
        handler.setLevel(Level.WARNING); // but this handler only prints WARNING and above
        logger.addHandler(handler);
        logger.setUseParentHandlers(false); // don't also use the default root console handler

        logger.fine("Detailed trace message");    // passes logger's level, blocked by handler's level
        logger.warning("Something looks off");     // passes both -- printed
        logger.severe("Critical failure");          // passes both -- printed
    }
}
```

**How to run:** `java LoggingCore.java`

Even though the logger's own level (`FINE`) would allow the `fine()` message through, the handler's stricter level (`WARNING`) filters it out before it reaches the console — a message is only actually emitted if it clears *both* the logger's level and the handler's level.

## 4. Diagram

<svg viewBox="0 0 620 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="a log call must clear the logger's level filter, then each attached handler's own level filter, before it is actually output">
  <rect x="8" y="8" width="604" height="134" rx="8" fill="#0d1117"/>
  <rect x="20" y="30" width="150" height="35" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="95" y="52" fill="#79c0ff" font-size="10" text-anchor="middle">logger.fine(msg)</text>

  <text x="185" y="52" fill="#8b949e" font-size="10">logger level FINE? →</text>

  <rect x="340" y="30" width="180" height="35" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="430" y="52" fill="#6db33f" font-size="10" text-anchor="middle">Handler (level WARNING)</text>

  <text x="20" y="100" fill="#f85149" font-size="9">FINE message passes logger, but is BLOCKED here (handler requires WARNING+)</text>
  <text x="20" y="120" fill="#6db33f" font-size="9">WARNING/SEVERE messages pass both gates and are printed</text>
</svg>

## 5. Runnable example

Scenario: a small order-processing routine's logging, evolved from unfiltered `println`-style logging, into structured logging with proper levels, into a production-style setup with a dedicated file handler, custom formatting, and level configuration separated from the code that logs.

### Level 1 — Basic

```java
public class OrderLoggingBasic {
    public static void main(String[] args) {
        processOrder("ORD-1001", 250.00);
        processOrder("ORD-1002", -5.00); // invalid, but only println-visible, no real severity
    }

    static void processOrder(String orderId, double amount) {
        System.out.println("Processing order " + orderId + " for $" + amount);
        if (amount < 0) {
            System.out.println("WARNING: invalid amount for " + orderId);
            return;
        }
        System.out.println("Order " + orderId + " completed");
    }
}
```

**How to run:** `java OrderLoggingBasic.java`

Every message looks identical to `println` — there's no severity distinction, no way to filter warnings from routine info messages, and no way to redirect this output anywhere other than standard out without changing the code.

### Level 2 — Intermediate

```java
import java.util.logging.Level;
import java.util.logging.Logger;

public class OrderLoggingIntermediate {
    private static final Logger logger = Logger.getLogger(OrderLoggingIntermediate.class.getName());

    public static void main(String[] args) {
        processOrder("ORD-1001", 250.00);
        processOrder("ORD-1002", -5.00);
    }

    static void processOrder(String orderId, double amount) {
        logger.info("Processing order " + orderId + " for $" + amount);
        if (amount < 0) {
            logger.warning("Invalid amount for " + orderId + ": " + amount);
            return;
        }
        logger.info("Order " + orderId + " completed");
    }
}
```

**How to run:** `java OrderLoggingIntermediate.java`

Now each message carries a real severity level (`INFO` vs. `WARNING`), which the default console handler renders distinctly and which downstream tooling could filter on — but everything still goes to the console with default formatting, and levels/destinations aren't yet configured separately from the logging calls themselves.

### Level 3 — Advanced

```java
import java.io.IOException;
import java.util.logging.*;

public class OrderLoggingAdvanced {
    private static final Logger logger = Logger.getLogger(OrderLoggingAdvanced.class.getName());

    public static void main(String[] args) throws IOException {
        logger.setUseParentHandlers(false); // don't duplicate onto the default console handler

        FileHandler fileHandler = new FileHandler("orders.log", true); // append mode
        fileHandler.setFormatter(new SimpleFormatter());
        fileHandler.setLevel(Level.INFO);
        logger.addHandler(fileHandler);

        ConsoleHandler consoleHandler = new ConsoleHandler();
        consoleHandler.setLevel(Level.WARNING); // console only shows problems
        logger.addHandler(consoleHandler);

        logger.setLevel(Level.INFO);

        processOrder("ORD-1001", 250.00);
        processOrder("ORD-1002", -5.00);

        fileHandler.close();
        System.out.println("Full log (including INFO) written to orders.log; only WARNING+ shown above.");
    }

    static void processOrder(String orderId, double amount) {
        logger.info("Processing order " + orderId + " for $" + amount);
        if (amount < 0) {
            logger.warning("Invalid amount for " + orderId + ": " + amount);
            return;
        }
        logger.info("Order " + orderId + " completed");
    }
}
```

**How to run:** `java OrderLoggingAdvanced.java`

Two handlers are attached with different levels — a `FileHandler` capturing everything at `INFO` and above into `orders.log` for a complete persistent record, and a `ConsoleHandler` restricted to `WARNING` and above so the terminal only shows problems needing attention — demonstrating how the same logging calls can be routed differently by destination without touching `processOrder` itself.

## 6. Walkthrough

Execution starts in `main`, which configures `logger` with two handlers (`fileHandler` at `INFO`, `consoleHandler` at `WARNING`) and sets the logger's own level to `INFO`, then calls `processOrder("ORD-1001", 250.00)`.

Inside `processOrder`, `logger.info(...)` is called. First, the logger checks its own level: `INFO` is permitted (the logger's level is `INFO`). The log record is then dispatched to each attached handler independently. `fileHandler`'s level is `INFO`, so this message passes and is written (via `SimpleFormatter`) to `orders.log`. `consoleHandler`'s level is `WARNING`, which is stricter than `INFO`, so this specific message is filtered out at the handler stage and never reaches the console. Since `amount` (250.00) is not negative, the method logs a second `INFO` message, `"Order ORD-1001 completed"`, following the identical path — written to the file, filtered from the console.

`main` then calls `processOrder("ORD-1002", -5.00)`. The initial `logger.info(...)` call again writes to the file only. Because `amount` is negative, `logger.warning(...)` is called instead of the completion message. This time, the record clears both the logger's level (`INFO` permits `WARNING`, since `WARNING` is a higher severity) and *both* handlers' levels (`fileHandler` at `INFO` and `consoleHandler` at `WARNING` both permit `WARNING`) — so this message is written to both `orders.log` and printed to the console.

After both calls, `main` closes `fileHandler` (flushing and releasing the file) and prints a final `println` note. The net effect: `orders.log` contains all four log calls (two `INFO` pairs plus the one `WARNING`), while the console only displayed the single `WARNING` message.

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="each log call is checked against the logger level, then independently against each handler's level, resulting in different messages reaching the file versus the console">
  <rect x="8" y="8" width="624" height="154" rx="8" fill="#0d1117"/>
  <text x="20" y="30" fill="#e6edf3" font-size="10">ORD-1001: info("Processing...") -&gt; logger OK -&gt; file: written, console: filtered (below WARNING)</text>
  <text x="20" y="52" fill="#e6edf3" font-size="10">ORD-1001: info("...completed") -&gt; same as above -&gt; file only</text>
  <text x="20" y="80" fill="#e6edf3" font-size="10">ORD-1002: info("Processing...") -&gt; file only, console filtered</text>
  <text x="20" y="102" fill="#f85149" font-size="10">ORD-1002: warning("Invalid amount...") -&gt; logger OK -&gt; file: written AND console: written</text>
  <text x="20" y="135" fill="#8b949e" font-size="10">Result: orders.log has 4 entries; console shows only the 1 WARNING message.</text>
</svg>

## 7. Gotchas & takeaways

> `Logger.getLogger(name)` returns a shared, potentially cached logger instance for a given name — attaching handlers or changing levels on a logger obtained this way affects every other piece of code that looks up a logger with that same name, which can produce surprising duplicate output if `setUseParentHandlers(false)` isn't set and handlers are added more than once.

- A log message must clear *both* the logger's level and the specific handler's level to actually be emitted by that handler — either one filtering it out is enough to suppress it there.
- `Logger.getLogger(ClassName.class.getName())` is the standard naming convention — it makes it easy to trace which class produced a given log line and to configure levels per-package or per-class.
- Different handlers can be configured with different levels and destinations simultaneously — a common pattern is a verbose file log alongside a terse, warnings-only console output.
- `setUseParentHandlers(false)` prevents messages from *also* being processed by the default root logger's handlers, avoiding duplicate output when you've added your own handlers.
- For substantial real-world projects, consider a logging facade (SLF4J) with a richer backend (Logback, Log4j2) — the core logger/level/handler concepts transfer directly, but those frameworks offer more flexible configuration and better performance characteristics.
