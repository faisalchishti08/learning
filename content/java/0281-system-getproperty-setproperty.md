---
card: java
gi: 281
slug: system-getproperty-setproperty
title: System.getProperty / setProperty
---

## 1. What it is

`System.getProperty(String key)` reads a JVM-wide configuration value called a "system property" — a key-value string pair holding information like the operating system name, the Java version, the user's home directory, or any custom value set at startup with `-Dkey=value` or programmatically with `System.setProperty(key, value)`. These properties are visible to the entire running JVM, not scoped to any particular class or thread.

```java
public class SystemPropertyDemo {
    public static void main(String[] args) {
        System.out.println("Java version: " + System.getProperty("java.version"));
        System.out.println("OS name: " + System.getProperty("os.name"));
        System.out.println("User home: " + System.getProperty("user.home"));

        System.setProperty("myapp.mode", "debug"); // set a CUSTOM property programmatically
        System.out.println("Custom property: " + System.getProperty("myapp.mode"));

        System.out.println("Missing property: " + System.getProperty("does.not.exist")); // returns null
    }
}
```

`System.getProperty("java.version")` and the other built-in keys retrieve information the JVM populates automatically at startup; `System.setProperty("myapp.mode", "debug")` sets a custom key-value pair the program itself controls, immediately readable afterward via `getProperty`; requesting a property that was never set returns `null` rather than throwing an exception.

## 2. Why & when

System properties provide a simple, JVM-wide mechanism for configuration values and environment information that any part of a program can read without needing them explicitly passed through every method call.

- **Reading environment and platform information** — properties like `java.version`, `os.name`, `user.home`, and `line.separator` (the platform-specific newline sequence) let code adapt its behaviour based on the environment it's actually running in, without hard-coding platform assumptions.
- **Configuring application behaviour without recompiling** — passing `-Dmyapp.environment=production` on the command line when launching the JVM lets an application's configuration change between runs without modifying or rebuilding the code, a common technique for controlling logging levels, feature flags, or environment-specific settings.
- **A simple, global alternative to threading configuration through every layer** — since system properties are visible JVM-wide, deeply nested code can read a configuration value directly via `System.getProperty` without every intermediate method needing to accept and pass along a configuration object — convenient, though this global visibility is also a real design tradeoff worth understanding (explored in the gotchas).

Use system properties for genuinely global, environment-level configuration (feature flags, environment names, platform-specific behaviour) set once at JVM startup or early in the application's life; avoid using them as a general-purpose way to pass data between unrelated parts of your own application, since their global, JVM-wide visibility makes code harder to reason about compared to explicitly passing configuration objects or parameters where practical.

## 3. Core concept

```java
public class SystemPropertyCore {
    static boolean isDebugMode() {
        return "true".equals(System.getProperty("myapp.debug")); // "true".equals(...) avoids NPE if property is missing
    }

    public static void main(String[] args) {
        System.out.println("Debug mode: " + isDebugMode()); // false, property not set yet

        System.setProperty("myapp.debug", "true");
        System.out.println("Debug mode: " + isDebugMode()); // true, now set
    }
}
```

`"true".equals(System.getProperty("myapp.debug"))` deliberately calls `.equals()` on the string literal `"true"` rather than on the (possibly `null`) result of `getProperty`, avoiding a `NullPointerException` if the property was never set — this is a standard, safe idiom whenever comparing a possibly-`null` value against a known non-null constant.

## 4. Diagram

<svg viewBox="0 0 600 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="System properties are JVM wide key value pairs, set via the minus D command line flag at startup or programmatically with setProperty, readable from anywhere in the running program with getProperty">
  <rect x="8" y="8" width="584" height="144" rx="8" fill="#0d1117"/>

  <rect x="40" y="20" width="220" height="35" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="150" y="42" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">java -Dmyapp.mode=debug App</text>

  <rect x="340" y="20" width="220" height="35" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="450" y="42" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">System.setProperty(k, v)</text>

  <line x1="150" y1="55" x2="300" y2="90" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="450" y1="55" x2="300" y2="90" stroke="#8b949e" stroke-width="1.5"/>

  <rect x="200" y="95" width="200" height="35" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="300" y="117" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">JVM-wide property table</text>

  <text x="300" y="145" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Readable anywhere via System.getProperty(key), regardless of where it was set.</text>
</svg>

System properties form a single, JVM-wide table, set at startup or programmatically, readable from anywhere in the running program.

## 5. Runnable example

Scenario: an application reading configuration via system properties, evolved from reading built-in properties into using a custom one for feature flagging, then hardened with a safe default-value pattern for missing properties.

### Level 1 — Basic

```java
public class SystemPropertyBasic {
    public static void main(String[] args) {
        System.out.println("Running on: " + System.getProperty("os.name"));
        System.out.println("Java version: " + System.getProperty("java.version"));
    }
}
```

**How to run:** `java SystemPropertyBasic.java`

Reads two built-in properties the JVM populates automatically at startup — no configuration needed, these are always available.

### Level 2 — Intermediate

Same idea, now setting and reading a custom feature-flag property, demonstrating properties set programmatically being visible immediately afterward.

```java
public class SystemPropertyIntermediate {
    static boolean isFeatureEnabled(String featureName) {
        return "true".equalsIgnoreCase(System.getProperty("feature." + featureName));
    }

    public static void main(String[] args) {
        System.out.println("New UI enabled? " + isFeatureEnabled("newUI")); // false, not set yet

        System.setProperty("feature.newUI", "true");
        System.out.println("New UI enabled? " + isFeatureEnabled("newUI")); // true, now set

        System.setProperty("feature.betaSearch", "false");
        System.out.println("Beta search enabled? " + isFeatureEnabled("betaSearch")); // false, explicitly set false
    }
}
```

**How to run:** `java SystemPropertyIntermediate.java`

`isFeatureEnabled` builds a property key dynamically (`"feature." + featureName`), demonstrating a common pattern for grouping related configuration under a shared prefix, all queried through the same `System.getProperty` mechanism.

### Level 3 — Advanced

Same feature-flag system, now with a safe default-value helper for properties that may or may not be set, and a demonstration of properties passed via `-D` at JVM startup (shown as command-line usage, since it happens before `main` even runs) versus set programmatically during execution.

```java
public class SystemPropertyAdvanced {
    static String getPropertyOrDefault(String key, String defaultValue) {
        String value = System.getProperty(key);
        return (value != null) ? value : defaultValue; // safe default pattern, avoids null propagating further
    }

    static int getIntPropertyOrDefault(String key, int defaultValue) {
        String value = System.getProperty(key);
        if (value == null) return defaultValue;
        try {
            return Integer.parseInt(value);
        } catch (NumberFormatException e) {
            System.err.println("Invalid integer property '" + key + "': " + value + ", using default");
            return defaultValue;
        }
    }

    public static void main(String[] args) {
        // Simulates a property that might have been passed via -Dmyapp.environment=... at startup
        String environment = getPropertyOrDefault("myapp.environment", "development");
        System.out.println("Environment: " + environment);

        int maxRetries = getIntPropertyOrDefault("myapp.maxRetries", 3);
        System.out.println("Max retries: " + maxRetries);

        // Now actually set one via setProperty, simulating what -D would have done at startup
        System.setProperty("myapp.maxRetries", "10");
        System.out.println("Max retries (after setProperty): " + getIntPropertyOrDefault("myapp.maxRetries", 3));

        System.setProperty("myapp.maxRetries", "not-a-number"); // simulates a malformed -D value
        System.out.println("Max retries (malformed): " + getIntPropertyOrDefault("myapp.maxRetries", 3));
    }
}
```

**How to run:** `java SystemPropertyAdvanced.java` (or, to see `-D` in action: `java -Dmyapp.environment=production SystemPropertyAdvanced`)

`getPropertyOrDefault` and `getIntPropertyOrDefault` both provide safe fallback values for properties that might be missing or, in the integer case, malformed — this is the standard, defensive pattern for reading configuration that might come from an external source (like a `-D` flag a user could set incorrectly) rather than assuming it's always present and well-formed.

## 6. Walkthrough

Trace `main` in `SystemPropertyAdvanced` when run with plain `java SystemPropertyAdvanced` (no `-D` flags passed).

**`getPropertyOrDefault("myapp.environment", "development")`.** `System.getProperty("myapp.environment")` returns `null` (never set, no `-D` flag passed). Since `value != null` is `false`, the method returns `"development"`, the default. Prints `"Environment: development"`.

**`getIntPropertyOrDefault("myapp.maxRetries", 3)`.** `System.getProperty("myapp.maxRetries")` returns `null`. Returns the default, `3`. Prints `"Max retries: 3"`.

**`System.setProperty("myapp.maxRetries", "10")`.** Sets the property programmatically.

**`getIntPropertyOrDefault("myapp.maxRetries", 3)` (second call).** `System.getProperty("myapp.maxRetries")` now returns `"10"` (not `null`). `Integer.parseInt("10")` succeeds, returning `10`. Prints `"Max retries (after setProperty): 10"`.

**`System.setProperty("myapp.maxRetries", "not-a-number")`.** Overwrites the property with malformed text.

**`getIntPropertyOrDefault("myapp.maxRetries", 3)` (third call).** `System.getProperty("myapp.maxRetries")` returns `"not-a-number"`. `Integer.parseInt("not-a-number")` throws `NumberFormatException`. Caught: prints a warning to `System.err` (`"Invalid integer property 'myapp.maxRetries': not-a-number, using default"`), and returns the default, `3`. Prints `"Max retries (malformed): 3"`.

```
getPropertyOrDefault("myapp.environment", "development"): property not set -> returns "development"
getIntPropertyOrDefault("myapp.maxRetries", 3):           property not set -> returns 3

setProperty("myapp.maxRetries", "10")
getIntPropertyOrDefault(...): property="10" -> parses -> returns 10

setProperty("myapp.maxRetries", "not-a-number")
getIntPropertyOrDefault(...): property="not-a-number" -> NumberFormatException -> warning, returns default 3
```

**Final output (standard output).**
```
Environment: development
Max retries: 3
Max retries (after setProperty): 10
Max retries (malformed): 3
```

**Standard error.**
```
Invalid integer property 'myapp.maxRetries': not-a-number, using default
```

## 7. Gotchas & takeaways

> **`System.getProperty(key)` returns `null` for a missing property rather than throwing an exception** — code that assumes a property is always present and calls a method on the result directly (like `.equals(...)` on the result, rather than the safer reversed form shown in this topic) risks a `NullPointerException` the moment that property happens not to be set. Always either provide a default value explicitly (as `getPropertyOrDefault` does) or use the "known-constant.equals(possiblyNull)" pattern for safe comparisons.

> **System properties are global and mutable for the entire JVM process, which makes them easy to misuse as a substitute for proper configuration passing between unrelated parts of a program** — since any code anywhere can call `System.setProperty` at any time, relying on them heavily can make an application's behaviour harder to trace and reason about, especially in larger codebases or when multiple libraries might set or read overlapping property keys. Reserve them for genuinely global, environment-level configuration, and prefer explicit parameter passing or dedicated configuration objects for application-specific data.

- System properties are JVM-wide key-value string pairs, set via `-Dkey=value` at startup or programmatically with `System.setProperty`, and readable anywhere in the running program with `System.getProperty`.
- Built-in properties (`java.version`, `os.name`, `user.home`, and more) provide environment and platform information the JVM populates automatically.
- `System.getProperty` returns `null` for a missing key rather than throwing, so always handle the possibility of a missing or malformed value explicitly with a safe default.
- System properties are globally visible and mutable across the entire JVM process — appropriate for genuine environment-level configuration, but easy to overuse as an implicit, hard-to-trace communication channel between unrelated parts of an application.
