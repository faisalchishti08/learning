---
card: microservices
gi: 362
slug: log-levels-dynamic-log-level-changes
title: "Log levels & dynamic log level changes"
---

## 1. What it is

**Log levels** (`TRACE`, `DEBUG`, `INFO`, `WARN`, `ERROR`, typically in increasing order of severity) let a service emit far more detail than is normally shown, while a configured threshold controls what actually gets logged — set the threshold to `INFO` and only `INFO`, `WARN`, and `ERROR` lines are emitted; `DEBUG` and `TRACE` lines are skipped entirely. **Dynamic log level changes** mean adjusting that threshold at runtime, on a live, already-running service, without a redeploy — so you can temporarily turn on verbose `DEBUG` logging for one specific service while investigating an issue, then turn it back down once you're done.

## 2. Why & when

Running every service permanently at `DEBUG` level would produce far more log volume than is affordable to store or search through in a [centralized log aggregation](0361-centralized-log-aggregation.md) system — most of that detail is never needed. But when investigating a specific, active issue, exactly that detailed `DEBUG` output is often precisely what's needed to understand what's happening. Requiring a full redeploy just to temporarily bump one service's log level (and another redeploy to revert it afterward) is slow and risky during an active incident — dynamic log level changes let you flip the threshold on a live instance in seconds, gather the detail you need, and flip it back, with zero deployment risk.

Run services at `INFO` (or higher) by default in production to control log volume and cost, and use a runtime mechanism (like Spring Boot Actuator's `/loggers` endpoint, covered later in this section) to temporarily raise a specific logger's level to `DEBUG` when actively investigating something — then lower it again once you're done, since leaving verbose logging on indefinitely defeats the cost-control purpose of having levels at all.

## 3. Core concept

Each log statement is tagged with a level; the logging framework compares that level against the currently configured threshold and only actually emits (and pays the cost of formatting and shipping) statements at or above that threshold. Because the threshold is just a piece of mutable runtime configuration, not baked into the compiled code, it can be changed while the process is running, immediately affecting which statements get emitted from that point forward.

```java
logger.debug("cache lookup for key={} took {}ms", key, elapsedMs); // SKIPPED entirely if threshold is INFO or higher
logger.info("order {} placed", orderId);                          // emitted at INFO threshold
logger.error("payment failed for order {}: {}", orderId, reason);  // always emitted unless threshold is above ERROR
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A vertical scale from TRACE at the bottom to ERROR at the top; a threshold line at INFO shows that TRACE and DEBUG statements below it are skipped, while INFO, WARN, and ERROR above it are emitted">
  <line x1="100" y1="30" x2="100" y2="150" stroke="#8b949e" stroke-width="1.5"/>
  <text x="180" y="35" fill="#8b949e" font-size="9" font-family="sans-serif">ERROR (always emitted)</text>
  <text x="180" y="60" fill="#8b949e" font-size="9" font-family="sans-serif">WARN</text>
  <line x1="90" y1="75" x2="400" y2="75" stroke="#79c0ff" stroke-dasharray="4,4"/>
  <text x="410" y="79" fill="#79c0ff" font-size="9" font-family="sans-serif">-- threshold: INFO --</text>
  <text x="180" y="90" fill="#3fb950" font-size="9" font-family="sans-serif">INFO (emitted)</text>
  <text x="180" y="115" fill="#f85149" font-size="9" font-family="sans-serif">DEBUG (SKIPPED, below threshold)</text>
  <text x="180" y="140" fill="#f85149" font-size="9" font-family="sans-serif">TRACE (SKIPPED, below threshold)</text>
</svg>

Only statements at or above the configured threshold are actually emitted; everything below it is silently skipped.

## 5. Runnable example

Scenario: a service logging at multiple levels, first with a fixed, unchangeable threshold requiring a full restart to adjust, then rebuilt with a dynamically adjustable threshold, and finally extended to change the threshold for one specific logger (not the whole service) while investigating a targeted issue.

### Level 1 — Basic

```java
// File: FixedThresholdRequiresRestart.java -- the log threshold is
// hardcoded; changing it means editing code and RESTARTING the process.
import java.util.*;

public class FixedThresholdRequiresRestart {
    enum Level { TRACE, DEBUG, INFO, WARN, ERROR }
    static final Level THRESHOLD = Level.INFO; // HARDCODED -- changing this requires a code change + restart

    static void log(Level level, String message) {
        if (level.ordinal() >= THRESHOLD.ordinal()) System.out.println("[" + level + "] " + message);
    }

    public static void main(String[] args) {
        log(Level.DEBUG, "cache lookup took 3ms"); // SKIPPED, below the hardcoded INFO threshold
        log(Level.INFO, "order placed");
        log(Level.ERROR, "payment failed");

        System.out.println("To see the DEBUG line above, we'd need to edit THRESHOLD in the code and RESTART the whole process.");
    }
}
```

How to run: `java FixedThresholdRequiresRestart.java`

`THRESHOLD` is a compile-time constant; the `DEBUG` call is silently skipped because `Level.DEBUG.ordinal()` (`1`) is less than `Level.INFO.ordinal()` (`2`). Seeing that debug detail during a live incident would require editing the code, rebuilding, and restarting the service — far too slow when you need the detail *right now*.

### Level 2 — Intermediate

```java
// File: DynamicallyAdjustableThreshold.java -- the threshold is MUTABLE
// state, changeable at runtime with NO restart needed.
import java.util.*;

public class DynamicallyAdjustableThreshold {
    enum Level { TRACE, DEBUG, INFO, WARN, ERROR }
    static Level currentThreshold = Level.INFO; // MUTABLE -- can change while the process is running

    static void setThreshold(Level newThreshold) { // simulates calling a runtime management endpoint
        System.out.println("Changing log threshold from " + currentThreshold + " to " + newThreshold + " (NO restart needed)");
        currentThreshold = newThreshold;
    }

    static void log(Level level, String message) {
        if (level.ordinal() >= currentThreshold.ordinal()) System.out.println("[" + level + "] " + message);
    }

    public static void main(String[] args) {
        log(Level.DEBUG, "cache lookup took 3ms"); // SKIPPED, threshold still INFO

        setThreshold(Level.DEBUG); // bump it up, live, e.g. while investigating an issue

        log(Level.DEBUG, "cache lookup took 8ms"); // NOW emitted -- same code, threshold changed live

        setThreshold(Level.INFO); // lower it back once done investigating
        log(Level.DEBUG, "cache lookup took 2ms"); // SKIPPED again
    }
}
```

How to run: `java DynamicallyAdjustableThreshold.java`

`currentThreshold` is a mutable variable rather than a constant. The first `DEBUG` call is skipped (threshold still `INFO`), but after `setThreshold(Level.DEBUG)` runs — standing in for calling a runtime management endpoint on a live process — the second `DEBUG` call *is* emitted, with no restart involved anywhere. Lowering the threshold back afterward correctly returns to skipping `DEBUG` lines, demonstrating the full cycle of temporarily raising verbosity and then reverting it.

### Level 3 — Advanced

```java
// File: PerLoggerThresholdOverride.java -- adjusts the threshold for ONE
// SPECIFIC logger (e.g. just the "payment" component under investigation)
// while leaving every OTHER logger at its normal, quieter default level.
import java.util.*;

public class PerLoggerThresholdOverride {
    enum Level { TRACE, DEBUG, INFO, WARN, ERROR }
    static Level defaultThreshold = Level.INFO;
    static Map<String, Level> perLoggerOverrides = new HashMap<>(); // e.g. {"payment": DEBUG}

    static void setLoggerLevel(String loggerName, Level level) {
        perLoggerOverrides.put(loggerName, level);
        System.out.println("Logger '" + loggerName + "' threshold set to " + level + " (all OTHER loggers unaffected)");
    }

    static void log(String loggerName, Level level, String message) {
        Level effectiveThreshold = perLoggerOverrides.getOrDefault(loggerName, defaultThreshold);
        if (level.ordinal() >= effectiveThreshold.ordinal()) System.out.println("[" + loggerName + "][" + level + "] " + message);
    }

    public static void main(String[] args) {
        log("order", Level.DEBUG, "validating order fields");     // SKIPPED, order logger at default INFO
        log("payment", Level.DEBUG, "attempting charge, retry 1"); // SKIPPED, payment logger ALSO still at default INFO

        setLoggerLevel("payment", Level.DEBUG); // bump up ONLY the payment logger, since that's what's under investigation

        log("order", Level.DEBUG, "validating order fields");     // STILL skipped -- order logger untouched
        log("payment", Level.DEBUG, "attempting charge, retry 2"); // NOW emitted -- payment logger specifically raised

        System.out.println("Only 'payment' logger's verbosity increased -- 'order' logger's volume stayed exactly the same, unaffected.");
    }
}
```

How to run: `java PerLoggerThresholdOverride.java`

`log` looks up `perLoggerOverrides.getOrDefault(loggerName, defaultThreshold)` to determine the *effective* threshold for each specific logger, falling back to the shared default when no override exists. Before `setLoggerLevel("payment", Level.DEBUG)` runs, both `"order"` and `"payment"` loggers use the default `INFO` threshold, so both `DEBUG` calls are skipped. After the override is set, only `"payment"`'s `DEBUG` call is emitted — `"order"`'s remains skipped, since its own entry in `perLoggerOverrides` was never touched, demonstrating targeted, per-component verbosity control rather than an all-or-nothing, service-wide toggle.

## 6. Walkthrough

Trace `PerLoggerThresholdOverride.main` in order. **First**, `log("order", Level.DEBUG, ...)` runs: `perLoggerOverrides.getOrDefault("order", defaultThreshold)` finds no entry for `"order"` yet, so it returns `defaultThreshold` (`INFO`). `Level.DEBUG.ordinal()` (`1`) is not `>=` `Level.INFO.ordinal()` (`2`), so nothing is printed.

**Next**, `log("payment", Level.DEBUG, ...)` runs the same way: no override exists for `"payment"` either, so it also falls back to `INFO`, and this `DEBUG` call is skipped too.

**Then**, `setLoggerLevel("payment", Level.DEBUG)` runs, inserting `"payment" -> Level.DEBUG` into `perLoggerOverrides` and printing a confirmation — critically, `"order"` is never touched by this call.

**Then**, `log("order", Level.DEBUG, ...)` runs again: `perLoggerOverrides.getOrDefault("order", defaultThreshold)` still finds no entry for `"order"`, so it still falls back to `INFO`, and this call is skipped exactly as before — unaffected by the change made to `"payment"`.

**Finally**, `log("payment", Level.DEBUG, ...)` runs again: this time `perLoggerOverrides.getOrDefault("payment", defaultThreshold)` finds the override, returning `Level.DEBUG`. Now `Level.DEBUG.ordinal()` (`1`) *is* `>=` `Level.DEBUG.ordinal()` (`1`), so the line is printed — demonstrating that only the specifically targeted logger's verbosity changed.

```
log(order, DEBUG)   -> effective=INFO (no override)    -> SKIPPED
log(payment, DEBUG) -> effective=INFO (no override yet) -> SKIPPED
setLoggerLevel(payment, DEBUG) -> perLoggerOverrides={payment: DEBUG}
log(order, DEBUG)   -> effective=INFO (still no override) -> SKIPPED (unaffected)
log(payment, DEBUG) -> effective=DEBUG (override applies) -> EMITTED
```

## 7. Gotchas & takeaways

> Forgetting to revert a temporarily-raised log level back to its normal default after an investigation is a common and costly mistake — a `DEBUG`-level logger left on indefinitely can quietly generate enormous, expensive log volume for weeks before anyone notices, especially on a high-traffic component like a payment or order logger.

- Log levels (`TRACE` through `ERROR`) let a service emit much more detail than normally shown, with a configured threshold controlling what's actually recorded and shipped.
- Dynamic log level changes let that threshold be adjusted on a live, running service — no redeploy needed — making it practical to temporarily raise verbosity during an active investigation.
- Per-logger overrides allow targeting just the specific component under investigation, keeping every other logger's volume and cost unchanged.
- Spring Boot Actuator's `/loggers` endpoint, covered in [Actuator /loggers for runtime log-level changes](0372-actuator-loggers-for-runtime-log-level-changes.md), is the concrete Spring mechanism for exactly this capability.
