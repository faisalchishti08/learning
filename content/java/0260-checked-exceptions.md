---
card: java
gi: 260
slug: checked-exceptions
title: Checked exceptions
---

## 1. What it is

A checked exception is any `Exception` subclass that is *not* a `RuntimeException` — the compiler forces any method that might throw one to either catch it or declare it in a `throws` clause, and forces every caller of that method to do the same. Common JDK examples include `IOException` (file and network operations) and `SQLException` (database operations) — both represent conditions genuinely outside the program's control that calling code is expected to plan for explicitly.

```java
import java.io.IOException;

public class CheckedExceptionDemo {
    static void readConfig() throws IOException { // MUST declare it — the compiler enforces this
        throw new IOException("config file not found");
    }

    public static void main(String[] args) {
        try {
            readConfig();
        } catch (IOException e) { // MUST catch it, or main itself would need "throws IOException"
            System.out.println("Failed to read config: " + e.getMessage());
        }
    }
}
```

`readConfig` declares `throws IOException` on its signature, and `main` is required to either catch `IOException` (as shown) or declare its own `throws IOException` — omitting both would be a compile error, since `IOException` is checked; this is the fundamental difference from the unchecked `RuntimeException` subtypes covered in the previous topic.

## 2. Why & when

Checked exceptions exist to force explicit acknowledgment of failure conditions that are genuinely outside a program's control and that callers should not be allowed to simply forget about.

- **Modeling conditions external to the program's own logic** — a file might not exist, a network connection might drop, a database might be unreachable: these are not programming bugs (unlike the conditions `RuntimeException` typically represents) but real-world failure modes that a well-designed program must plan for.
- **Compiler-enforced acknowledgment** — by making these exceptions checked, Java ensures that a method calling `readConfig()` cannot accidentally forget that config reading might fail; it must explicitly decide to catch the failure or propagate the responsibility up its own `throws` clause, making the possibility of failure visible directly in the code's structure.
- **A documented, discoverable failure contract** — a method's `throws` clause is part of its public API, visible to anyone reading its signature; this makes checked exceptions a form of self-documenting code, telling callers exactly what external failure modes they need to be prepared to handle.

Design your own methods to throw checked exceptions specifically for conditions genuinely outside the program's control that callers should be forced to consider (I/O, network, external system failures) — reserve unchecked exceptions (the previous topic) for programming errors and precondition violations; this checked-versus-unchecked distinction, deliberately chosen based on what kind of failure you're modeling, is one of the most consequential design decisions in Java exception handling.

## 3. Core concept

```java
import java.io.IOException;

class FileReaderService {
    String readFile(String path) throws IOException { // declares the checked exception it might throw
        if (path == null || path.isBlank()) {
            throw new IOException("invalid path: " + path); // a condition truly outside this method's control
        }
        return "file contents for: " + path; // simplified stand-in for real file reading
    }
}

public class CheckedCore {
    public static void main(String[] args) throws IOException { // propagating: main declares it too
        FileReaderService service = new FileReaderService();
        System.out.println(service.readFile("config.txt"));
    }
}
```

`main` itself declares `throws IOException`, choosing to propagate the responsibility rather than catch it directly — this is a legal way to satisfy the compiler's requirement, though for `main` specifically it means an uncaught `IOException` would terminate the program with a printed stack trace, exactly like an unchecked exception would if left uncaught; the checked/unchecked distinction only affects *compile-time* enforcement, not runtime behaviour when actually uncaught.

## 4. Diagram

<svg viewBox="0 0 600 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A checked exception forces every method in the call chain to either catch it or declare throws, the compiler rejects code that does neither, unlike an unchecked RuntimeException which requires no such declaration">
  <rect x="8" y="8" width="584" height="154" rx="8" fill="#0d1117"/>

  <rect x="40" y="20" width="220" height="35" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
  <text x="150" y="42" fill="#f85149" font-size="9" text-anchor="middle" font-family="monospace">readConfig() throws IOException</text>

  <line x1="150" y1="55" x2="150" y2="80" stroke="#8b949e" stroke-width="1.5"/>
  <text x="150" y="75" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">caller MUST react</text>

  <rect x="40" y="85" width="100" height="30" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="90" y="105" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">catch it</text>

  <rect x="160" y="85" width="100" height="30" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="210" y="105" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">declare throws</text>

  <text x="450" y="70" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Neither option chosen?</text>
  <text x="450" y="88" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Compile error —</text>
  <text x="450" y="106" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">this is what "checked" means.</text>

  <text x="300" y="140" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Every method in the chain must explicitly acknowledge a checked exception, one way or the other.</text>
</svg>

Every method in the call chain must explicitly catch or declare a checked exception — the compiler enforces this.

## 5. Runnable example

Scenario: a small configuration-loading system using checked exceptions to model genuinely external failure modes, evolved from a single throwing method into a multi-layer call chain, then hardened with a custom checked exception and multiple recovery strategies.

### Level 1 — Basic

```java
public class CheckedExceptionBasic {
    static class ConfigNotFoundException extends Exception { // extends Exception directly -> CHECKED
        ConfigNotFoundException(String message) { super(message); }
    }

    static String loadConfig(String path) throws ConfigNotFoundException {
        if (!path.equals("valid-config.txt")) {
            throw new ConfigNotFoundException("no config found at: " + path);
        }
        return "debug=true";
    }

    public static void main(String[] args) {
        try {
            System.out.println(loadConfig("missing.txt"));
        } catch (ConfigNotFoundException e) {
            System.out.println("Failed: " + e.getMessage());
        }
    }
}
```

**How to run:** `java CheckedExceptionBasic.java`

`ConfigNotFoundException extends Exception` directly (not `RuntimeException`), making it checked; `loadConfig` must declare `throws ConfigNotFoundException`, and `main` must either catch it (as shown) or declare its own `throws` clause — the compiler enforces this at every level.

### Level 2 — Intermediate

Same configuration system, now with the checked exception propagating through an intermediate method, demonstrating that every method in the chain must acknowledge it, one way or another.

```java
public class CheckedExceptionIntermediate {
    static class ConfigNotFoundException extends Exception {
        ConfigNotFoundException(String message) { super(message); }
    }

    static String loadConfig(String path) throws ConfigNotFoundException {
        if (!path.equals("valid-config.txt")) {
            throw new ConfigNotFoundException("no config found at: " + path);
        }
        return "debug=true";
    }

    // This intermediate method does NOT catch it -- it re-declares throws, passing the obligation upward
    static String getDebugSetting(String path) throws ConfigNotFoundException {
        String config = loadConfig(path); // if this throws, getDebugSetting propagates it further
        return config.split("=")[1];
    }

    public static void main(String[] args) {
        try {
            System.out.println("Debug setting: " + getDebugSetting("missing.txt"));
        } catch (ConfigNotFoundException e) {
            System.out.println("Could not determine debug setting: " + e.getMessage());
        }
    }
}
```

**How to run:** `java CheckedExceptionIntermediate.java`

`getDebugSetting` calls `loadConfig`, which can throw `ConfigNotFoundException`; rather than catching it, `getDebugSetting` simply re-declares `throws ConfigNotFoundException` on its own signature, passing the responsibility further up the call chain to `main`, which finally catches it — this chain of declarations is exactly how a checked exception's obligation propagates through multiple layers of method calls.

### Level 3 — Advanced

Same system, now with two different checked exceptions from two different sources, handled with separate recovery strategies — one triggers a fallback default, the other is fatal and terminates with a clear message — demonstrating realistic, differentiated handling of multiple checked failure modes.

```java
public class CheckedExceptionAdvanced {
    static class ConfigNotFoundException extends Exception {
        ConfigNotFoundException(String message) { super(message); }
    }

    static class ConfigCorruptException extends Exception {
        ConfigCorruptException(String message) { super(message); }
    }

    static String loadConfig(String path) throws ConfigNotFoundException, ConfigCorruptException {
        if (path.equals("missing.txt")) {
            throw new ConfigNotFoundException("no config found at: " + path);
        }
        if (path.equals("corrupt.txt")) {
            throw new ConfigCorruptException("config at " + path + " is unreadable garbage");
        }
        return "debug=true";
    }

    static String getDebugSettingWithFallback(String path) {
        try {
            return loadConfig(path).split("=")[1];
        } catch (ConfigNotFoundException e) {
            System.out.println("Config missing, using default: " + e.getMessage());
            return "false"; // recoverable: fall back to a safe default
        } catch (ConfigCorruptException e) {
            // Corruption is treated as fatal here -- wrapped and rethrown as unchecked, since callers
            // of THIS method should not be forced to handle a scenario this severe on every call
            throw new IllegalStateException("Cannot continue with a corrupt config: " + e.getMessage(), e);
        }
    }

    public static void main(String[] args) {
        System.out.println("Setting for missing.txt: " + getDebugSettingWithFallback("missing.txt"));

        try {
            getDebugSettingWithFallback("corrupt.txt");
        } catch (IllegalStateException e) {
            System.out.println("Fatal error: " + e.getMessage());
            System.out.println("Caused by: " + e.getCause().getMessage()); // the original checked exception
        }
    }
}
```

**How to run:** `java CheckedExceptionAdvanced.java`

`getDebugSettingWithFallback` handles the two checked exceptions completely differently: `ConfigNotFoundException` is recoverable, so it falls back to a safe default and returns normally; `ConfigCorruptException` is treated as unrecoverable, so it is wrapped in an unchecked `IllegalStateException` (preserving the original as its "cause," accessible via `getCause()`) and rethrown — this deliberately converts a checked failure into an unchecked one at a point where the method's own callers should not be forced to handle it on every single call.

## 6. Walkthrough

Trace both calls to `getDebugSettingWithFallback` in `CheckedExceptionAdvanced.main`.

**`getDebugSettingWithFallback("missing.txt")`.** Inside the `try`, `loadConfig("missing.txt")` is called: `path.equals("missing.txt")` is `true`, so `ConfigNotFoundException("no config found at: missing.txt")` is thrown. This is caught by the first `catch` clause: it prints `"Config missing, using default: no config found at: missing.txt"`, then returns the literal string `"false"` as a safe fallback. Back in `main`, this is printed as `"Setting for missing.txt: false"`.

**`getDebugSettingWithFallback("corrupt.txt")`.** Inside the `try`, `loadConfig("corrupt.txt")` is called: this path doesn't match `"missing.txt"`, but does match `"corrupt.txt"`, so `ConfigCorruptException("config at corrupt.txt is unreadable garbage")` is thrown. This is caught by the second `catch` clause, which constructs a new `IllegalStateException` with a combined message and passes the original `ConfigCorruptException` as the *cause* (the second argument to the `IllegalStateException` constructor), then throws this new, unchecked exception. Since `getDebugSettingWithFallback` does not declare `throws` for `IllegalStateException` (it's unchecked, so it doesn't need to), this propagates directly out to `main`.

**Back in `main`'s second `try`/`catch`.** The `IllegalStateException` is caught. `e.getMessage()` returns `"Cannot continue with a corrupt config: config at corrupt.txt is unreadable garbage"`. `e.getCause()` returns the original `ConfigCorruptException` object, and calling `.getMessage()` on *that* returns `"config at corrupt.txt is unreadable garbage"` again (the original message, accessed through the cause chain).

```
getDebugSettingWithFallback("missing.txt"):
  loadConfig -> throws ConfigNotFoundException -> caught -> prints message, returns "false"
  main prints: "Setting for missing.txt: false"

getDebugSettingWithFallback("corrupt.txt"):
  loadConfig -> throws ConfigCorruptException -> caught -> wrapped in new IllegalStateException(cause=original)
  -> IllegalStateException propagates to main, uncaught by getDebugSettingWithFallback itself
  main catches IllegalStateException:
    e.getMessage() -> "Cannot continue with a corrupt config: config at corrupt.txt is unreadable garbage"
    e.getCause().getMessage() -> "config at corrupt.txt is unreadable garbage"
```

**Final output.**
```
Setting for missing.txt: false
Config missing, using default: no config found at: missing.txt
Fatal error: Cannot continue with a corrupt config: config at corrupt.txt is unreadable garbage
Caused by: config at corrupt.txt is unreadable garbage
```
(Note: the "Config missing..." line prints *before* the "Setting for missing.txt..." line in program order, since it happens inside `getDebugSettingWithFallback` before that method returns its value to be printed by `main` — the actual terminal output order reflects this: the inner print happens first, then the outer one uses the returned value.)

## 7. Gotchas & takeaways

> **Wrapping a checked exception in an unchecked one (as `getDebugSettingWithFallback` does with `IllegalStateException`) is a common, deliberate pattern for converting "this failure is outside our control at a low level" into "this is now a serious problem the immediate caller shouldn't be forced to handle on every call."** Always pass the original exception as the *cause* (the second constructor argument) so the full failure chain remains visible via `getCause()` for debugging — silently discarding the original exception when wrapping it destroys valuable diagnostic information.

> **Overusing checked exceptions for conditions that are really just programming errors is a common design mistake** — forcing every caller to catch or declare an exception for something that should simply never happen if the code is correct (as opposed to a genuine external failure) adds compile-time ceremony without real safety benefit; this is part of why many modern Java APIs and libraries increasingly favor unchecked exceptions even for some conditions that could arguably be checked.

- A checked exception is any `Exception` subclass that does not extend `RuntimeException`; the compiler forces every method in the call chain to catch it or declare it via `throws`.
- Checked exceptions are best reserved for conditions genuinely outside the program's control (I/O failures, network issues, external system errors) that callers should be forced to explicitly consider.
- A method can either catch a checked exception itself or propagate the obligation by declaring its own `throws` clause, passing the responsibility to its own callers.
- Wrapping a caught checked exception in a new unchecked exception (preserving the original via the "cause" parameter) is a standard pattern for converting a low-level, externally-forced failure into a higher-level, unchecked one.
