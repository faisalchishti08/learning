---
card: java
gi: 700
slug: enable-c-14-in-jdk-source
title: Enable C++14 in JDK source
---

## 1. What it is

**JEP 347**, delivered in **Java 16**, permits OpenJDK's own **native C++ source code** — HotSpot, the VM's garbage collectors and JIT compilers, and other native JDK components — to use **C++14** language features, and requires that all supported platform toolchains be able to compile it as such. Before this JEP, OpenJDK's native code was restricted to a much older, conservative subset of C++ (effectively C++98/03-era style) so it would compile cleanly across every compiler the project supported. This is entirely an internal build-toolchain change to the JDK's own implementation language; it adds nothing to the Java language or any Java API.

## 2. Why & when

HotSpot and the rest of the JDK's native components are written in C++, not Java, and for a long time that C++ code deliberately avoided modern language features to stay compatible with older compilers across all the platforms OpenJDK supports. As those compiler versions aged out and modern C++ standards became widely supported, that self-imposed restriction started costing the OpenJDK developers real productivity — features like generic lambdas, binary literals, digit separators in numeric literals, and relaxed `constexpr` rules make native code easier to write and maintain, and other native codebases had been using them for years. JEP 347 raised the *minimum* required language level to C++14 for building the JDK itself, letting HotSpot contributors use these features once every supported build toolchain could handle them. If you only ever write Java code, this JEP has zero visible effect — it matters exclusively to people who build OpenJDK from source or contribute to HotSpot's native internals.

## 3. Core concept

```bash
# Before JEP 347 — OpenJDK's own C++ build effectively targeted a
# conservative C++98/03-style subset for maximum toolchain compatibility.

# From Java 16 onward — the JDK build requires and allows C++14:
g++ -std=c++14 -c hotspot_file.cpp -o hotspot_file.o
```

Nothing here is a Java API — it is a build-toolchain requirement for compiling HotSpot's own native source, expressed as a compiler standard flag.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Before Java 16, HotSpot native source was restricted to a conservative C++03-style subset; Java 16 onward it may use C++14 features, and every supported build toolchain must accept them">
  <rect x="20" y="20" width="280" height="160" rx="8" fill="#1c2430" stroke="#8b949e"/>
  <text x="160" y="42" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Before Java 16</text>
  <text x="160" y="70" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">HotSpot .cpp source</text>
  <text x="160" y="95" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">restricted to C++03-style subset</text>
  <text x="160" y="120" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">no generic lambdas, no binary literals</text>
  <text x="160" y="145" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">chosen for widest compiler compatibility</text>

  <rect x="340" y="20" width="280" height="160" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="480" y="42" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">Java 16+</text>
  <text x="480" y="70" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">HotSpot .cpp source</text>
  <text x="480" y="95" fill="#3fb950" font-size="10" text-anchor="middle" font-family="sans-serif">C++14 features allowed</text>
  <text x="480" y="120" fill="#3fb950" font-size="9" text-anchor="middle" font-family="sans-serif">generic lambdas, binary literals, ...</text>
  <text x="480" y="145" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">all supported toolchains must compile it</text>
</svg>

The minimum required C++ language level for building HotSpot's own native source rises from a C++03-style subset to C++14.

## 5. Runnable example

Scenario: since JEP 347 is a native-toolchain requirement rather than a Java API, the most faithful runnable example is a small Java-based "toolchain capability checker" — the same kind of check the OpenJDK build system effectively needed once it started requiring C++14: does the local C++ compiler actually accept C++14 syntax? The example starts by compiling one tiny C++14 snippet through a single hard-coded compiler invocation, then extends to detecting which compiler is actually available on the machine, then finally builds a small compatibility matrix across several C++14 features and several `-std=` levels — mirroring exactly the kind of build-toolchain verification JEP 347's adoption required across every platform OpenJDK supports.

### Level 1 — Basic

```java
// File: Cpp14Basic.java
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;

public class Cpp14Basic {
    public static void main(String[] args) throws IOException, InterruptedException {
        Path source = Files.createTempFile("check", ".cpp");
        Files.writeString(source, """
                // A generic lambda: a C++14 feature (not legal in C++03/C++11).
                #include <iostream>
                int main() {
                    auto add = [](auto a, auto b) { return a + b; };
                    std::cout << add(2, 3) << std::endl;
                    return 0;
                }
                """);

        Process compile = new ProcessBuilder("g++", "-std=c++14", source.toString(), "-o", "check_out")
                .redirectErrorStream(true)
                .start();
        String output = new String(compile.getInputStream().readAllBytes());
        int exitCode = compile.waitFor();

        System.out.println("Compile exit code: " + exitCode);
        if (!output.isBlank()) System.out.println("Compiler output: " + output);
        System.out.println(exitCode == 0 ? "C++14 generic lambda compiled successfully." : "Compile failed.");
    }
}
```

**How to run:**
```
java Cpp14Basic.java
```

Expected output shape (assuming `g++` is installed and on the `PATH`):
```
Compile exit code: 0
C++14 generic lambda compiled successfully.
```

### Level 2 — Intermediate

```java
// File: Cpp14Detect.java
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;

public class Cpp14Detect {

    static String findCompiler() {
        for (String candidate : List.of("g++", "clang++", "c++")) {
            try {
                Process check = new ProcessBuilder(candidate, "--version")
                        .redirectErrorStream(true).start();
                if (check.waitFor() == 0) return candidate;
            } catch (IOException | InterruptedException ignored) {
                // Not found or not runnable; try the next candidate.
            }
        }
        return null;
    }

    public static void main(String[] args) throws IOException, InterruptedException {
        String compiler = findCompiler();
        if (compiler == null) {
            System.out.println("No C++ compiler found on PATH; skipping toolchain check.");
            return;
        }
        System.out.println("Using compiler: " + compiler);

        Path source = Files.createTempFile("check", ".cpp");
        Files.writeString(source, """
                #include <iostream>
                int main() {
                    auto add = [](auto a, auto b) { return a + b; }; // generic lambda
                    int million = 1'000'000;                          // digit separators
                    std::cout << add(2, 3) << " " << million << std::endl;
                    return 0;
                }
                """);

        Process compile = new ProcessBuilder(compiler, "-std=c++14", source.toString(), "-o", "check_out")
                .redirectErrorStream(true).start();
        String output = new String(compile.getInputStream().readAllBytes());
        int exitCode = compile.waitFor();

        System.out.println("Compile exit code: " + exitCode);
        if (!output.isBlank()) System.out.println("Compiler output: " + output);
    }
}
```

**How to run:**
```
java Cpp14Detect.java
```

Expected output shape (compiler choice depends on what's installed; on macOS, `clang++` is typically found first):
```
Using compiler: clang++
Compile exit code: 0
```

### Level 3 — Advanced

```java
// File: Cpp14Matrix.java
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

public class Cpp14Matrix {

    record Feature(String name, String snippet) {}

    static String findCompiler() {
        for (String candidate : List.of("g++", "clang++", "c++")) {
            try {
                Process check = new ProcessBuilder(candidate, "--version")
                        .redirectErrorStream(true).start();
                if (check.waitFor() == 0) return candidate;
            } catch (IOException | InterruptedException ignored) {
                // Not found or not runnable; try the next candidate.
            }
        }
        return null;
    }

    static boolean compiles(String compiler, String std, String body) {
        try {
            Path source = Files.createTempFile("check", ".cpp");
            Files.writeString(source, "int main() { " + body + " return 0; }");
            Process compile = new ProcessBuilder(compiler, "-std=" + std, source.toString(), "-o", "check_out")
                    .redirectErrorStream(true).start();
            compile.getInputStream().readAllBytes();
            return compile.waitFor() == 0;
        } catch (IOException | InterruptedException e) {
            return false;
        }
    }

    public static void main(String[] args) {
        String compiler = findCompiler();
        if (compiler == null) {
            System.out.println("No C++ compiler found on PATH; skipping toolchain check.");
            return;
        }
        System.out.println("Using compiler: " + compiler);

        List<Feature> features = List.of(
                new Feature("generic lambda", "auto f = [](auto a, auto b){ return a + b; }; f(1, 2);"),
                new Feature("digit separators", "int million = 1'000'000; (void)million;"),
                new Feature("binary literals", "int mask = 0b1010; (void)mask;")
        );
        List<String> standards = List.of("c++03", "c++11", "c++14");

        Map<String, Map<String, Boolean>> matrix = new LinkedHashMap<>();
        for (Feature feature : features) {
            Map<String, Boolean> row = new LinkedHashMap<>();
            for (String std : standards) {
                row.put(std, compiles(compiler, std, feature.snippet()));
            }
            matrix.put(feature.name(), row);
        }

        System.out.printf("%-20s", "feature");
        for (String std : standards) System.out.printf("%-8s", std);
        System.out.println();

        for (var entry : matrix.entrySet()) {
            System.out.printf("%-20s", entry.getKey());
            for (String std : standards) {
                System.out.printf("%-8s", entry.getValue().get(std) ? "OK" : "fail");
            }
            System.out.println();
        }
    }
}
```

**How to run:**
```
java Cpp14Matrix.java
```

Expected output shape (a real compiler will typically accept generic lambdas and binary literals only from `c++14` onward, since those are C++14 features; digit separators are also C++14):
```
Using compiler: clang++
feature             c++03   c++11   c++14   
generic lambda      fail    fail    OK      
digit separators    fail    fail    OK      
binary literals     fail    fail    OK      
```

## 6. Walkthrough

1. `Cpp14Matrix.main` first calls `findCompiler()`, which tries `g++`, `clang++`, and `c++` in turn by running `<compiler> --version` and checking the exit code — this mirrors how a build system has to locate a usable compiler on each platform before it can enforce any language-standard requirement.
2. If no compiler is found, the program prints a clear message and returns normally rather than failing — since this check is purely illustrative and shouldn't require a C++ toolchain to be installed just to demonstrate the concept.
3. Three small `Feature` records each pair a feature name with a one-line C++ snippet that only compiles under C++14 or later: a generic lambda (`auto` parameters), digit separators in an integer literal (`1'000'000`), and a binary literal (`0b1010`).
4. For each feature, `compiles(...)` writes that snippet into a temporary `.cpp` file wrapped in a trivial `main`, then invokes the compiler three times — once per candidate `-std=` value (`c++03`, `c++11`, `c++14`) — recording whether each invocation exits successfully.
5. The nested loop builds a `matrix`: for every feature, a row mapping each language standard to whether it compiled. This is exactly the shape of information the OpenJDK build maintainers needed before JEP 347 landed — confirmation that a given feature (and, by extension, a chunk of proposed HotSpot code using it) would or would not compile under each candidate minimum standard, across every supported toolchain.
6. The final loop prints the matrix as a simple table. In a real run, every feature fails under `c++03` and `c++11` and succeeds only under `c++14`, which is the empirical justification for JEP 347's decision: raising the minimum required standard to C++14 was the only way to let HotSpot's C++ source use any of these constructs.

```
findCompiler()  -> pick first working compiler from [g++, clang++, c++]
for each feature (generic lambda, digit separators, binary literals):
    for each standard (c++03, c++11, c++14):
        compile a minimal snippet using that feature under that standard
        record pass/fail
print feature x standard compatibility matrix
```

## 7. Gotchas & takeaways

> This example shells out to a real system C++ compiler via `ProcessBuilder`; if none of `g++`, `clang++`, or `c++` is installed, the program detects that and exits cleanly with a message instead of crashing — but on a typical macOS or Linux development machine, `clang++` or `g++` is usually already present.

- JEP 347 is a **build-toolchain requirement for OpenJDK's own native C++ source** (HotSpot, native JDK libraries) — it does not add anything to the Java language or any `java.*`/`javax.*` API, and has zero effect on code you write in Java.
- The practical trigger for caring about this JEP is contributing to HotSpot or building OpenJDK from source: from Java 16 onward, the build assumes a C++14-capable compiler on every supported platform, and native contributions may freely use C++14 features like generic lambdas, binary literals, and digit separators.
- The "does this compiler accept these features under this standard" check performed here is a simplified, application-level version of exactly the kind of cross-platform toolchain verification the JEP process requires before raising a minimum language-standard bar — real OpenJDK toolchain requirements are tracked and enforced through the project's own build configuration, not a Java program.
- Raising a minimum compiler-standard requirement is a one-way door for a project the size of OpenJDK: it has to hold across every platform and CI configuration the project supports, which is why such changes go through a full JEP process rather than being an incidental code change.
- If you're evaluating whether your own native (JNI or JNA) code could similarly adopt a newer C++ standard, the same pattern applies: verify the *actual* minimum compiler version across every platform you ship on before committing your codebase to using newer language features.
