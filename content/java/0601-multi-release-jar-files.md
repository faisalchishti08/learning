---
card: java
gi: 601
slug: multi-release-jar-files
title: Multi-release JAR files
---

## 1. What it is

Multi-release JAR files (MR-JARs), introduced in Java 9, allow a single `.jar` file to contain different versions of the same class for different Java runtime versions. The JAR's root directory holds the base version (compatible with the oldest supported JDK), and a `META-INF/versions/N/` directory structure holds version-specific overrides for JDK `N` and above. When the JAR is loaded, the JVM automatically selects the class from the highest version directory that does not exceed the current runtime version — older JDKs see only the base classes.

## 2. Why & when

Library maintainers face a chronic problem: they want to adopt new JDK APIs (e.g. `StackWalker` in Java 9, records in Java 14, pattern matching in Java 17) to improve performance or functionality, but they cannot abandon users on older JDKs. Before MR-JARs, the options were (a) maintain separate artifact versions per JDK (explodes the release matrix), (b) use reflection to conditionally call new APIs (verbose, error-prone, and slow), or (c) forgo the new APIs entirely (stifling innovation). Multi-release JARs solve this by packaging all versions into a single artifact: the JVM picks the right one at load time, and users download one `.jar` regardless of their JDK version.

## 3. Core concept

```
my-lib.jar
├── com/example/Utils.class          ← Base version (compatible with JDK 8+)
├── META-INF/
│   └── MANIFEST.MF                  ← Must contain: Multi-Release: true
│   └── versions/
│       ├── 9/
│       │   └── com/example/Utils.class   ← JDK 9+ override
│       ├── 11/
│       │   └── com/example/Utils.class   ← JDK 11+ override
│       └── 17/
│           └── com/example/Utils.class   ← JDK 17+ override
```

The base class in `com/example/Utils.class` targets the minimum supported JDK. On JDK 10, the JVM loads `META-INF/versions/9/com/example/Utils.class` (the highest version ≤ 10). On JDK 17, it loads `META-INF/versions/17/com/example/Utils.class`. On JDK 8 (which doesn't understand MR-JARs), it ignores the `versions/` directory entirely and loads the base class.

## 4. Diagram

<svg viewBox="0 0 600 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Multi-release JAR selects the highest version-specific class ≤ the current JVM version">
  <rect x="20" y="10" width="560" height="180" rx="8" fill="#1c2430" stroke="#6db33f"/>

  <text x="30" y="35" fill="#e6edf3" font-size="11" font-family="sans-serif">my-lib.jar (Multi-Release: true)</text>

  <rect x="30" y="50" width="180" height="30" rx="4" fill="#0d1117" stroke="#6db33f"/>
  <text x="120" y="70" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace">com/example/Utils.class</text>
  <text x="220" y="70" fill="#8b949e" font-size="9" font-family="sans-serif">(base)</text>

  <rect x="30" y="86" width="180" height="30" rx="4" fill="#0d1117" stroke="#79c0ff"/>
  <text x="120" y="106" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="monospace">versions/9/.../Utils.class</text>
  <text x="220" y="106" fill="#8b949e" font-size="9" font-family="sans-serif">JDK 9+</text>

  <rect x="30" y="122" width="180" height="30" rx="4" fill="#0d1117" stroke="#f0883e"/>
  <text x="120" y="142" fill="#f0883e" font-size="11" text-anchor="middle" font-family="monospace">versions/17/.../Utils.class</text>
  <text x="220" y="142" fill="#8b949e" font-size="9" font-family="sans-serif">JDK 17+</text>

  <text x="290" y="70" fill="#8b949e" font-size="9" font-family="sans-serif">JDK 8 loads this</text>
  <text x="290" y="106" fill="#8b949e" font-size="9" font-family="sans-serif">JDK 9–16 loads this</text>
  <text x="290" y="142" fill="#8b949e" font-size="9" font-family="sans-serif">JDK 17+ loads this</text>

  <text x="30" y="178" fill="#8b949e" font-size="9" font-family="sans-serif">Rule: load the highest version N where N ≤ current JDK version. No matching version → load base.</text>
</svg>

The JVM compares its version to the `versions/N/` directories and picks the best match.

## 5. Runnable example

Scenario: a utility class that computes a hash — starting with a basic single-version JAR, extending to a multi-release build with a Java 9+ `StackWalker` enhancement, and finally demonstrating the runtime version selection and fallback behaviour through explicit version checks.

### Level 1 — Basic

```java
// File: HashUtils.java  (base version — JDK 8 compatible)
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;

public class HashUtils {
    public static String sha256(String input) {
        try {
            MessageDigest md = MessageDigest.getInstance("SHA-256");
            byte[] hash = md.digest(input.getBytes(StandardCharsets.UTF_8));
            StringBuilder hex = new StringBuilder();
            for (byte b : hash) {
                hex.append(String.format("%02x", b));
            }
            return hex.toString();
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
    }

    // This method will be overridden in version-specific classes
    public static String versionInfo() {
        return "HashUtils (base/JDK 8 compatible)";
    }

    public static void main(String[] args) {
        System.out.println(versionInfo());
        System.out.println("SHA-256 of 'hello': " + sha256("hello"));
    }
}
```

**How to run:** `java HashUtils.java`

Expected output:
```
HashUtils (base/JDK 8 compatible)
SHA-256 of 'hello': 2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824
```

The base version works on any JDK 8+. It uses only JDK 8 APIs (`MessageDigest`, `StandardCharsets`, `StringBuilder`). The `versionInfo()` method reports which version is loaded at runtime.

### Level 2 — Intermediate

```java
// File: HashUtils9.java  (version-specific: JDK 9+ override for META-INF/versions/9/)
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.HexFormat;  // Java 17 API — but the concept is version-gated

public class HashUtils {
    // Same contract, different implementation using newer APIs
    public static String sha256(String input) {
        try {
            MessageDigest md = MessageDigest.getInstance("SHA-256");
            byte[] hash = md.digest(input.getBytes(StandardCharsets.UTF_8));

            // Use StackWalker (Java 9+) to log the caller for diagnostics
            String caller = StackWalker.getInstance()
                .walk(frames -> frames.skip(1).findFirst()
                    .map(f -> f.getClassName())
                    .orElse("?"));
            System.out.println("  [Debug] sha256 called by: " + caller);

            StringBuilder hex = new StringBuilder();
            for (byte b : hash) {
                hex.append(String.format("%02x", b));
            }
            return hex.toString();
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
    }

    public static String versionInfo() {
        return "HashUtils (JDK 9+) with StackWalker diagnostics";
    }

    public static void main(String[] args) {
        System.out.println(versionInfo());
        System.out.println("SHA-256 of 'hello': " + sha256("hello"));
    }
}
```

**How to run (standalone, simulating the override):** `java HashUtils9.java`

Expected output:
```
HashUtils (JDK 9+) with StackWalker diagnostics
  [Debug] sha256 called by: HashUtils9
SHA-256 of 'hello': 2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824
```

The real-world concern added: using a version-specific API (`StackWalker`, JDK 9+) in the override. In a real MR-JAR build, this file would be compiled with `javac --release 9` and placed at `META-INF/versions/9/com/example/HashUtils.class`. On JDK 9 and above, this version is loaded instead of the base — providing the diagnostic `StackWalker` logging. On JDK 8, the JVM ignores the `versions/` directory and loads the base class (which lacks the diagnostic logging but works correctly).

### Level 3 — Advanced

```java
// File: MRJarDemo.java  (demonstrates runtime version detection, simulating MR-JAR behaviour)
public class MRJarDemo {

    // Simulates what the JVM does when loading a multi-release JAR class
    static String simulateVersionResolution() {
        int jdkVersion = Runtime.version().feature();  // e.g. 9, 11, 17, 21

        // Simulated available versions in a hypothetical MR-JAR
        int[] availableVersions = {9, 11, 17};

        int selected = 0;  // 0 means base
        for (int v : availableVersions) {
            if (v <= jdkVersion) {
                selected = v;  // highest version ≤ current JDK
            }
        }
        return selected > 0 ? "versions/" + selected : "base";
    }

    public static void main(String[] args) {
        int jdkVersion = Runtime.version().feature();
        System.out.println("Running on JDK " + jdkVersion);
        System.out.println("MR-JAR resolution path: " + simulateVersionResolution());

        System.out.println("\nAvailable version directories in our MR-JAR:");
        System.out.println("  base    → JDK 8 compatible (no new APIs)");
        System.out.println("  versions/9  → JDK 9+ (StackWalker diagnostics)");
        System.out.println("  versions/11 → JDK 11+ (HttpClient for telemetry)");
        System.out.println("  versions/17 → JDK 17+ (records, sealed classes)");

        System.out.println("\nOn this JDK, the JVM would load:");
        String path = simulateVersionResolution();
        System.out.println("  " + path + "/com/example/HashUtils.class");

        System.out.println("\nBenefits:");
        System.out.println("  - One .jar for all JDK versions");
        System.out.println("  - No reflection or conditional loading in code");
        System.out.println("  - Older JDKs never see incompatible bytecode");
    }
}
```

**How to run:** `java MRJarDemo.java`

Expected output (JDK 17 example):
```
Running on JDK 17
MR-JAR resolution path: versions/17

Available version directories in our MR-JAR:
  base    → JDK 8 compatible (no new APIs)
  versions/9  → JDK 9+ (StackWalker diagnostics)
  versions/11 → JDK 11+ (HttpClient for telemetry)
  versions/17 → JDK 17+ (records, sealed classes)

On this JDK, the JVM would load:
  versions/17/com/example/HashUtils.class

Benefits:
  - One .jar for all JDK versions
  - No reflection or conditional loading in code
  - Older JDKs never see incompatible bytecode
```

The production-flavoured demonstration: `Runtime.version().feature()` (JDK 9+) tells you the current major version. The version resolution logic is exactly what the JVM does: iterates through available `versions/N/` directories and picks the highest `N ≤ currentVersion`. This simulation shows the decision-making process without requiring an actual JAR build, making the concept concrete and verifiable.

## 6. Walkthrough

Tracing the `HashUtils.sha256("hello")` call in the Level 2 (JDK 9+ version):

1. `HashUtils.sha256("hello")` is invoked. On JDK 9+, the JVM's class loader resolved `HashUtils` to `META-INF/versions/9/com/example/HashUtils.class` — the version-specific override — because JDK 9 ≤ 17 (the current version) but there is no higher match (e.g. `versions/17/HashUtils.class`). On JDK 8, only the base `HashUtils.class` is loaded because JDK 8 doesn't understand the `versions/` directory structure.

2. The `sha256` method begins executing with `input = "hello"`.

3. `MessageDigest.getInstance("SHA-256")` creates the SHA-256 digest engine — a standard JDK API available since JDK 1.4, safe for base and override both.

4. `input.getBytes(StandardCharsets.UTF_8)` converts the string to UTF-8 bytes: `[104, 101, 108, 108, 111]`.

5. `md.digest(bytes)` computes the SHA-256 hash, producing a `byte[32]` containing the hash bytes.

6. **Key version-specific behaviour**: `StackWalker.getInstance().walk(frames -> ...)` is called. This is a JDK 9+ API, so it only compiles and runs on the version-specific class. The walker skips frame 0 (internal) and frame 1 (the `sha256` method itself), landing on the caller — in `main`, it's `HashUtils9`. The diagnostic line `"[Debug] sha256 called by: HashUtils9"` is printed.

7. The `StringBuilder` loop converts each byte to a two-character hex string, producing the final hash: `"2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"`.

8. `versionInfo()` (in the override) returns `"HashUtils (JDK 9+) with StackWalker diagnostics"` — confirming the override is active.

```
Request: HashUtils.sha256("hello")

┌─ JDK 9+ (loaded from versions/9/) ────────────────────┐
│  1. input.getBytes(UTF_8)       → byte[] (UTF-8)      │
│  2. MessageDigest.digest()      → byte[32] (SHA-256)  │
│  3. StackWalker (JDK 9+ API)    → caller class name   │
│  4. StringBuilder hex conversion → "2cf24dba..."      │
│  Returns: SHA-256 hex string                          │
└───────────────────────────────────────────────────────┘

┌─ JDK 8 (loaded from root/base) ──────────────────────┐
│  1-2: same as above                                   │
│  3: no StackWalker — skips diagnostic log            │
│  4: same hex conversion                               │
│  Returns: same SHA-256 hex string                     │
└──────────────────────────────────────────────────────┘

Same result, different internal path — transparent to the caller.
```

## 7. Gotchas & takeaways

> The version-specific class must have the **exact same public API** as the base class — same class name, same package, same public method signatures. If the override adds, removes, or changes a public method signature, the JVM will load the class but callers compiled against the base version will get `NoSuchMethodError` at runtime. This is the MR-JAR equivalent of the "same binary interface" contract.

- `META-INF/MANIFEST.MF` must contain the line `Multi-Release: true` (case-sensitive, followed by a newline). Without this header, the JVM treats the JAR as a standard single-release JAR and ignores the `versions/` directory entirely — no error, just silent fallback to base classes.
- The version number in `versions/N/` must be a **major JDK version** (9, 10, 11, 17, 21, etc.) — the JVM's version resolution ignores pre-release and update suffixes, matching only the feature release number.
- `jar --create --file my-lib.jar --main-class=com.example.Main --multi-release=9` lets the `jar` tool automatically sort classes into `versions/9/` when using `--release 9` during compilation. Build tools like Maven and Gradle have dedicated MR-JAR support in their assembly plugins.
- MR-JARs are not limited to new APIs — an override can also use a different algorithm, a faster data structure, or a JDK-specific optimisation. The only rule is the public API contract must remain the same.
- The classloader caches the resolved class per JAR — once `HashUtils` is loaded from `versions/9/`, subsequent references to `HashUtils` in the same classloader use the same resolved version. You cannot "switch versions" mid-execution. 