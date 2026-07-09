---
card: java
gi: 586
slug: try-with-resources-on-effectively-final-vars
title: Try-with-resources on effectively-final vars
---

## 1. What it is

Since Java 9, a try-with-resources statement can use a **variable declared before the try block** directly, as long as that variable is final or effectively final — instead of requiring the resource to be freshly declared inside the `try (...)` parentheses. `try (existingResource) { ... }` is now legal, where before Java 9 only `try (Resource r = existingResource) { ... }` (redeclaring it under a new, often redundant name) was allowed.

## 2. Why & when

Before Java 9, try-with-resources syntax required a *declaration* inside the parentheses — `try (BufferedReader reader = getReader())`. If you already had a resource variable from earlier code (perhaps obtained through a method that needed to do other setup first, or a resource passed in as a parameter), you were forced to redeclare it with a new, usually meaningless variable name just to satisfy the syntax: `try (BufferedReader reader2 = reader)`. This was pure boilerplate — the resource already existed, already had a name, and didn't need a second one. Java 9 removed this requirement for variables that are final or effectively final (never reassigned after initialization), letting `try (reader) { ... }` close the existing variable directly, with no redundant redeclaration.

## 3. Core concept

```java
BufferedReader reader = new BufferedReader(new FileReader("data.txt")); // declared BEFORE try

try (reader) { // Java 9+: use the existing effectively-final variable directly
    System.out.println(reader.readLine());
} // reader.close() is still called automatically here, exactly as if newly declared
```

`reader` must never be reassigned anywhere after its initial assignment for this to compile — the exact same "effectively final" rule that governs which local variables can be captured by a lambda or anonymous class.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Java 9 lets try-with-resources reference an existing effectively-final variable directly instead of requiring a fresh declaration">
  <text x="20" y="25" fill="#8b949e" font-size="11" font-family="sans-serif">Before Java 9 — forced redeclaration:</text>
  <rect x="20" y="35" width="600" height="30" rx="6" fill="#1c2430" stroke="#f85149"/>
  <text x="320" y="55" fill="#f85149" font-size="10" text-anchor="middle" font-family="monospace">try (BufferedReader reader2 = reader) { ... }</text>

  <text x="20" y="95" fill="#8b949e" font-size="11" font-family="sans-serif">Java 9+ — use the existing variable directly:</text>
  <rect x="20" y="105" width="600" height="30" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="320" y="125" fill="#6db33f" font-size="10" text-anchor="middle" font-family="monospace">try (reader) { ... }</text>
</svg>

Same automatic-close guarantee either way — only the boilerplate redeclaration disappears.

## 5. Runnable example

Scenario: reading a small config file whose reader is obtained through a small setup method before the try block — starting with the pre-Java-9 forced-redeclaration style, then simplifying with the direct-variable form, then handling multiple pre-existing resources at once, closed in reverse declaration order.

### Level 1 — Basic

```java
import java.io.*;

public class TryResourcesOldStyle {
    public static void main(String[] args) throws IOException {
        File tempFile = File.createTempFile("config", ".txt");
        tempFile.deleteOnExit();
        try (PrintWriter writer = new PrintWriter(tempFile)) {
            writer.println("timeout=30");
        }

        BufferedReader reader = new BufferedReader(new FileReader(tempFile)); // declared BEFORE try
        try (BufferedReader reader2 = reader) { // pre-Java-9 style: forced redeclaration
            System.out.println(reader2.readLine());
        }
    }
}
```

**How to run:** `java TryResourcesOldStyle.java`

Expected output:
```
timeout=30
```

`reader` is created outside the `try`, then immediately redeclared as `reader2` purely to satisfy the pre-Java-9 try-with-resources syntax, which required a fresh declaration inside the parentheses. `reader2` is never used for anything except being the syntactically-required name — a small but real piece of boilerplate this whole topic exists to remove.

### Level 2 — Intermediate

```java
import java.io.*;

public class TryResourcesModern {
    public static void main(String[] args) throws IOException {
        File tempFile = File.createTempFile("config", ".txt");
        tempFile.deleteOnExit();
        try (PrintWriter writer = new PrintWriter(tempFile)) {
            writer.println("timeout=30");
        }

        BufferedReader reader = new BufferedReader(new FileReader(tempFile)); // declared BEFORE try
        try (reader) { // Java 9+: use the existing effectively-final variable directly
            System.out.println(reader.readLine());
        }
    }
}
```

**How to run:** `java TryResourcesModern.java`

Expected output:
```
timeout=30
```

The real-world concern this adds: `try (reader)` uses the existing `reader` variable directly — no `reader2`, no redundant redeclaration. This compiles because `reader` is effectively final: it's assigned exactly once (at declaration) and never reassigned anywhere afterward. `reader.close()` is still called automatically when the `try` block exits, identical behavior to Level 1, just without the boilerplate.

### Level 3 — Advanced

```java
import java.io.*;
import java.util.*;

public class TryResourcesMultiple {
    static List<String> closeLog = new ArrayList<>();

    static class LoggingResource implements AutoCloseable {
        final String name;
        LoggingResource(String name) { this.name = name; }
        @Override public void close() { closeLog.add(name); }
    }

    public static void main(String[] args) {
        LoggingResource dbConnection = new LoggingResource("db-connection");
        LoggingResource fileHandle = new LoggingResource("file-handle");
        LoggingResource cacheClient = new LoggingResource("cache-client");

        try (dbConnection; fileHandle; cacheClient) { // THREE pre-existing resources, semicolon-separated
            System.out.println("Using all three resources...");
        }

        System.out.println("Closed in order: " + closeLog);
    }
}
```

**How to run:** `java TryResourcesMultiple.java`

Expected output:
```
Using all three resources...
Closed in order: [cache-client, file-handle, db-connection]
```

This handles the production-flavoured case of **multiple pre-existing resources** in a single `try`, semicolon-separated exactly like multiple fresh declarations would be: `try (dbConnection; fileHandle; cacheClient)`. All three variables must independently be effectively final. `closeLog` records the actual close order, confirming that resources close in **reverse** of their listed order — `cacheClient` (listed last) closes first, `dbConnection` (listed first) closes last — the same LIFO closing guarantee try-with-resources has always provided for freshly-declared resources, unaffected by whether the variables were pre-existing or newly declared.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. Three `LoggingResource` instances are created and assigned to `dbConnection`, `fileHandle`, and `cacheClient` — all three variables are effectively final (assigned exactly once, never reassigned), satisfying the requirement for direct use in try-with-resources.

`try (dbConnection; fileHandle; cacheClient) { ... }` is entered. Unlike a normal `try` block, this doesn't create any new variables or run any additional code at entry beyond what already happened when the three `LoggingResource` instances were constructed — the `try (...)` clause here is purely registering these three existing objects as resources to be closed automatically, in a specific, guaranteed order, once the block exits.

The block body runs: `System.out.println("Using all three resources...")` executes and prints its message. As the block exits normally (no exception thrown), the try-with-resources machinery begins closing each resource.

```
Resource close order (always REVERSE of declaration/listing order):

try (dbConnection; fileHandle; cacheClient) { ... }
                                    |
                                    v  closes FIRST
                          cacheClient.close()  -> closeLog: [cache-client]
                                    |
                                    v  closes SECOND
                            fileHandle.close()  -> closeLog: [cache-client, file-handle]
                                    |
                                    v  closes LAST
                          dbConnection.close()  -> closeLog: [cache-client, file-handle, db-connection]
```

`cacheClient.close()` runs first, appending `"cache-client"` to `closeLog`. `fileHandle.close()` runs next, appending `"file-handle"`. `dbConnection.close()` runs last, appending `"db-connection"`. This reverse-of-declaration-order closing is deliberate and matches how try-with-resources has always worked, even with freshly-declared resources: it mirrors the intuitive "last acquired, first released" pattern (analogous to how nested try blocks or stack unwinding work), ensuring a resource that might depend on another resource still being open (e.g., `cacheClient` potentially depending on `dbConnection` being alive) is closed before the resource it might depend on.

`main`'s final line prints `closeLog`, confirming the order: `[cache-client, file-handle, db-connection]` — exactly the reverse of how the three resources were listed in the `try (...)` clause.

## 7. Gotchas & takeaways

> The variable used directly in `try (variable)` must be **effectively final** — assigned exactly once and never reassigned anywhere in its scope, even in code paths that don't actually execute. If a variable is reassigned anywhere after its declaration (even conditionally, even in a branch never actually taken at runtime), it loses effectively-final status and can no longer be used this way — the compiler enforces this purely syntactically, based on the code as written, not based on what actually happens at runtime.

- This feature only changes how a resource variable gets *into* the try-with-resources clause — the actual guarantee (resources closed automatically, in reverse order, even if an exception is thrown) is completely unchanged from pre-Java-9 try-with-resources behavior.
- A resource used this way can be a field access, a method parameter, or any other effectively-final local variable — not just a plain local variable declared with `var` or an explicit type; the only requirement is effective finality, not any particular kind of declaration.
- Mixing pre-existing and freshly-declared resources in the same `try (...)` clause is legal: `try (existingReader; BufferedWriter writer = new BufferedWriter(...))` combines both forms, semicolon-separated, in any order.
- If the variable is *not* effectively final (it's reassigned somewhere), the compiler rejects `try (variable)` with a clear error explaining that the expression is not a variable that's final or effectively final — the fix is either to stop reassigning it, or to fall back to the classic redeclaration form (`try (Resource r = variable)`), which still works exactly as it always did.
- This is one of several Java 9 changes explicitly aimed at reducing small, common boilerplate patterns (alongside private interface methods, covered separately) rather than adding new fundamental capability — the language behavior is identical either way; only the ceremony required to express it is reduced.
