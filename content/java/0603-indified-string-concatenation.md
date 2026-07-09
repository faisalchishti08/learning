---
card: java
gi: 603
slug: indified-string-concatenation
title: Indified string concatenation
---

## 1. What it is

Indified string concatenation is a JDK 9 change to how the Java compiler translates string concatenation expressions (`"a" + b + "c"`) into bytecode. Instead of generating a `StringBuilder` chain (as JDK 8 and earlier did), the compiler now emits an `invokedynamic` instruction that delegates the concatenation strategy to a bootstrap method in `java.lang.invoke.StringConcatFactory`. At runtime, the JVM selects the optimal concatenation strategy — which may be `StringBuilder`, byte-array copying, or direct `Unsafe` memory operations — based on the shape and size of the expression, and the target platform's characteristics. The result is faster concatenation without changing any Java source code.

## 2. Why & when

The old `StringBuilder` approach was a reasonable default when introduced in JDK 5, but it has fixed costs: a `StringBuilder` object allocation, a `char[]` buffer (which may need to grow), and method-call overhead for every `.append()`. For small concatenations (two or three parts), the allocation cost dominates. For large concatenations, the buffer growth strategy guesses the initial capacity poorly (16 characters by default), causing multiple array copies. `invokedynamic` makes the strategy a runtime decision — the JVM can bake in constants, pre-size the result array exactly, use specialised copy routines, and inline the entire concatenation into a single tight sequence at the call site. This is the compiler and JVM working together to optimise what is, empirically, one of the most common operations in Java programs.

## 3. Core concept

```java
// Source code (unchanged):
String msg = "User " + name + " logged in at " + timestamp;

// JDK 8 bytecode (conceptual):
//   new StringBuilder
//   append("User ")
//   append(name)
//   append(" logged in at ")
//   append(timestamp)
//   toString()

// JDK 9 bytecode (conceptual):
//   invokedynamic #concat (User , name, logged in at, timestamp)
//   → runtime resolves to optimal strategy via StringConcatFactory
```

The compiler translates the `+` expression into a single `invokedynamic` call site. The bootstrap method (`StringConcatFactory.makeConcatWithConstants` for expressions with constant parts, or `makeConcat` for purely dynamic ones) returns a `CallSite` that links to a method handle — a strategy function. On first invocation, the JVM picks and links the strategy; subsequent calls go directly to the optimised code.

## 4. Diagram

<svg viewBox="0 0 580 180" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Indified string concatenation: compiler emits invokedynamic, runtime picks optimal strategy">
  <rect x="20" y="10" width="540" height="160" rx="8" fill="#1c2430" stroke="#6db33f"/>

  <rect x="40" y="30" width="160" height="40" rx="4" fill="#0d1117" stroke="#79c0ff"/>
  <text x="120" y="55" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="monospace">"a" + b + "c"</text>

  <text x="215" y="55" fill="#8b949e" font-size="10" font-family="monospace">──┤javac├──►</text>

  <rect x="300" y="30" width="130" height="40" rx="4" fill="#0d1117" stroke="#f0883e"/>
  <text x="365" y="55" fill="#f0883e" font-size="10" text-anchor="middle" font-family="monospace">invokedynamic</text>

  <text x="445" y="55" fill="#8b949e" font-size="10" font-family="monospace">──►</text>

  <rect x="440" y="25" width="110" height="50" rx="4" fill="#6db33f" stroke="#6db33f"/>
  <text x="495" y="43" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">Strategy</text>
  <text x="495" y="58" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">Selection</text>
  <text x="495" y="72" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">at runtime</text>

  <rect x="40" y="95" width="160" height="30" rx="4" fill="#1c2430" stroke="#6db33f" stroke-dasharray="4"/>
  <text x="120" y="114" fill="#6db33f" font-size="10" text-anchor="middle" font-family="monospace">byte[] copy + pre-size</text>
  <rect x="220" y="95" width="160" height="30" rx="4" fill="#1c2430" stroke="#f85149" stroke-dasharray="4"/>
  <text x="300" y="114" fill="#f85149" font-size="10" text-anchor="middle" font-family="monospace">StringBuilder fallback</text>
  <rect x="400" y="95" width="140" height="30" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-dasharray="4"/>
  <text x="470" y="114" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">Unsafe direct copy</text>

  <text x="30" y="155" fill="#8b949e" font-size="8" font-family="sans-serif">Bootstrap: StringConcatFactory.makeConcatWithConstants( ... )</text>
</svg>

`javac` doesn't pick the strategy — it defers to `invokedynamic`, and the JVM chooses the best approach at link time.

## 5. Runnable example

Scenario: comparing concatenation approaches with microbenchmarks — starting with the traditional explicit `StringBuilder` approach, extending to a comparison of the old implicit `StringBuilder` vs the new indified concatenation, and finally demonstrating when each strategy is effective through varying input sizes.

### Level 1 — Basic

```java
// File: ConcatDemo.java
public class ConcatDemo {
    public static void main(String[] args) {
        String user = "Alice";
        int score = 95;

        // This looks the same as always — but the bytecode is different in JDK 9+
        String msg = "User " + user + " scored " + score + " points";

        System.out.println(msg);

        // The old explicit way still works (and may still be faster in some cases)
        StringBuilder sb = new StringBuilder();
        sb.append("User ").append(user).append(" scored ").append(score).append(" points");
        System.out.println(sb.toString());
    }
}
```

**How to run:** `java ConcatDemo.java`

Expected output:
```
User Alice scored 95 points
User Alice scored 95 points
```

Identical output from both approaches. The `+` operator version now compiles to `invokedynamic` instead of `StringBuilder` chain. You cannot observe this difference from the output — it is a bytecode-level and runtime-performance change. Both approaches produce the same result.

### Level 2 — Intermediate

```java
// File: ConcatBenchmark.java
public class ConcatBenchmark {

    static String concatInline(String a, String b, int n) {
        return "Value[" + n + "]: " + a + " + " + b;
    }

    static String concatStringBuilder(String a, String b, int n) {
        return new StringBuilder()
            .append("Value[").append(n).append("]: ")
            .append(a).append(" + ").append(b)
            .toString();
    }

    public static void main(String[] args) {
        int iterations = 1_000_000;
        String a = "hello";
        String b = "world";

        // Warm up
        for (int i = 0; i < 10_000; i++) {
            concatInline(a, b, i);
            concatStringBuilder(a, b, i);
        }

        // Benchmark inline (+)
        long start = System.nanoTime();
        String last1 = null;
        for (int i = 0; i < iterations; i++) {
            last1 = concatInline(a, b, i);
        }
        long inlineTime = System.nanoTime() - start;

        // Benchmark StringBuilder
        start = System.nanoTime();
        String last2 = null;
        for (int i = 0; i < iterations; i++) {
            last2 = concatStringBuilder(a, b, i);
        }
        long sbTime = System.nanoTime() - start;

        System.out.println("Concatenation benchmark (" + iterations + " iterations):\n");
        System.out.printf("  Inline (+)        %8d ns (result: %s)%n", inlineTime, last1);
        System.out.printf("  StringBuilder     %8d ns (result: %s)%n", sbTime, last2);

        if (inlineTime < sbTime) {
            System.out.printf("\n  Inline is %.0f%% faster%n",
                100.0 * (sbTime - inlineTime) / sbTime);
        } else {
            System.out.printf("\n  StringBuilder is %.0f%% faster%n",
                100.0 * (inlineTime - sbTime) / inlineTime);
        }

        System.out.println("\n(In JDK 9+, the + operator uses invokedynamic,");
        System.out.println(" potentially beating or matching explicit StringBuilder.)");
    }
}
```

**How to run:** `java ConcatBenchmark.java`

Expected output (timings vary, but inline should be close to or faster than StringBuilder):
```
Concatenation benchmark (1000000 iterations):

  Inline (+)           45000000 ns (result: Value[999999]: hello + world)
  StringBuilder        48000000 ns (result: Value[999999]: hello + world)

  Inline is 6% faster

(In JDK 9+, the + operator uses invokedynamic,
 potentially beating or matching explicit StringBuilder.)
```

The real-world comparison: the `+` operator (using `invokedynamic` in JDK 9+) vs explicit `StringBuilder`. In JDK 8, the explicit `StringBuilder` was often faster because the compiler-generated `StringBuilder` chain had suboptimal initial capacity. In JDK 9+, the `invokedynamic` approach can pre-size the result and use optimised copying, making it at least as fast as — and often faster than — manual `StringBuilder`.

### Level 3 — Advanced

```java
// File: ConcatAnalysis.java
import java.lang.invoke.*;
import java.util.StringJoiner;
import java.util.stream.Collectors;
import java.util.stream.IntStream;

public class ConcatAnalysis {

    // Different concatenation strategies
    static String viaPlus(String prefix, int id, String suffix) {
        return prefix + "[" + id + "]" + suffix;  // invokedynamic in JDK 9+
    }

    static String viaStringBuilder(String prefix, int id, String suffix) {
        return new StringBuilder(prefix.length() + suffix.length() + 20)
            .append(prefix).append('[').append(id).append(']').append(suffix)
            .toString();
    }

    static String viaStringFormat(String prefix, int id, String suffix) {
        return String.format("%s[%d]%s", prefix, id, suffix);
    }

    static String viaStringJoin(String prefix, int id, String suffix) {
        return String.join("", prefix, "[", String.valueOf(id), "]", suffix);
    }

    public static void main(String[] args) {
        int iterations = 200_000;
        String prefix = "Log-";
        String suffix = "-end";

        record Result(String method, long nanos, String sample) {}

        Result[] results = new Result[4];

        // Warm up all
        for (int i = 0; i < 5000; i++) {
            viaPlus(prefix, i, suffix);
            viaStringBuilder(prefix, i, suffix);
            viaStringFormat(prefix, i, suffix);
            viaStringJoin(prefix, i, suffix);
        }

        // Benchmark each
        long start = System.nanoTime();
        String s = null;
        for (int i = 0; i < iterations; i++) s = viaPlus(prefix, i, suffix);
        results[0] = new Result("Plus (+)", System.nanoTime() - start, s);

        start = System.nanoTime();
        for (int i = 0; i < iterations; i++) s = viaStringBuilder(prefix, i, suffix);
        results[1] = new Result("StringBuilder", System.nanoTime() - start, s);

        start = System.nanoTime();
        for (int i = 0; i < iterations; i++) s = viaStringFormat(prefix, i, suffix);
        results[2] = new Result("String.format", System.nanoTime() - start, s);

        start = System.nanoTime();
        for (int i = 0; i < iterations; i++) s = viaStringJoin(prefix, i, suffix);
        results[3] = new Result("String.join", System.nanoTime() - start, s);

        // Find fastest for relative comparison
        long fastest = results[0].nanos();
        for (var r : results) if (r.nanos() < fastest) fastest = r.nanos();

        System.out.println("Concatenation strategy comparison (" + iterations + " iterations):\n");
        System.out.printf("%-18s %10s %10s   %s%n", "Strategy", "Time (ns)", "Relative", "Sample");
        System.out.println("-".repeat(65));
        for (var r : results) {
            System.out.printf("%-18s %10d   %5.1fx   %s%n",
                r.method(), r.nanos(), (double)r.nanos() / fastest, r.sample());
        }

        System.out.println("\nKey insight:");
        System.out.println("  + operator (invokedynamic)  → compiler/runtime optimised, zero-API-change");
        System.out.println("  String.format                → slowest (parses format string every call)");
        System.out.println("  StringBuilder                → explicit control, good when building in loops");
        System.out.println("  String.join                  → good for joining known pieces, no delimiter needed");
    }
}
```

**How to run:** `java ConcatAnalysis.java`

Expected output (timings vary):
```
Concatenation strategy comparison (200000 iterations):

Strategy            Time (ns)   Relative   Sample
-----------------------------------------------------------------
Plus (+)             8900000       1.0x   Log-[199999]-end
StringBuilder        9200000       1.0x   Log-[199999]-end
String.format       48000000       5.4x   Log-[199999]-end
String.join         15000000       1.7x   Log-[199999]-end

Key insight:
  + operator (invokedynamic)  → compiler/runtime optimised, zero-API-change
  String.format                → slowest (parses format string every call)
  StringBuilder                → explicit control, good when building in loops
  String.join                  → good for joining known pieces, no delimiter needed
```

The production-flavoured analysis: comparing four concatenation strategies in a single benchmark. In JDK 9+, the `+` operator (via `invokedynamic`) consistently matches or beats explicit `StringBuilder` because the JVM can pre-size the result and use optimised copy routines. `String.format` is far slower because it parses the format pattern on every call — it should only be used when formatting needs are complex. `String.join` sits between them. The key insight: for simple concatenation, just use `+` — the JVM has your back.

## 6. Walkthrough

Tracing `viaPlus("Log-", 42, "-end")` through compilation and execution in JDK 9+:

**Compilation time (`javac`)**:

1. The Java compiler encounters `prefix + "[" + id + "]" + suffix`.

2. Instead of emitting `new StringBuilder(); append(prefix); append("["); append(id); ...`, `javac` emits a single `invokedynamic` instruction with a bootstrap method reference to `StringConcatFactory.makeConcatWithConstants(...)`.

3. The constant parts (`"["` and `"]"`) are baked into the bootstrap arguments as constants — the runtime strategy can inline them directly without loading them from the constant pool at each call.

4. The dynamic parts (`prefix`, `id`, `suffix`) are passed as arguments to the strategy method handle.

**Runtime (first call — linking)**:

5. The `invokedynamic` call site is unlinked (no strategy yet). The JVM calls the bootstrap method: `StringConcatFactory.makeConcatWithConstants(lookup, name, concatType, recipe, constants)`.

6. The bootstrap method inspects the "recipe" — a string describing the concatenation shape: `"\u0001[ \u0002]\u0001"` where `\u0001` represents a dynamic argument and `\u0002` represents a constant. It sees constant parts (`[`, `]`) and dynamic parts (3 arguments).

7. The factory selects the optimal strategy based on the recipe and argument types. For this small concatenation (5 parts total, with constants), it generates a strategy that:
   - Computes the exact total length: `prefix.length() + 1 + String.valueOf(id).length() + 1 + suffix.length()`.
   - Allocates a single `byte[]` of exactly that size (no `StringBuilder` guesswork).
   - Copies each part into the byte array using specialised routines (for Latin-1 strings, direct `System.arraycopy`; for mixed, per-character copy).
   - Wraps the byte array in a new `String`.

8. The strategy is linked to the call site. Subsequent calls skip the bootstrap and go directly to the optimised method handle.

**Execution (linked call)**:

9. `prefix` is `"Log-"` (4 chars), `id` is 42 (string form `"42"`, 2 chars), `suffix` is `"-end"` (4 chars). Total length = 4 + 1 + 2 + 1 + 4 = 12.

10. A `byte[12]` is allocated. `"Log-"` is copied (4 bytes), `[` is copied (1 byte), `"42"` is copied (2 bytes), `]` is copied (1 byte), `"-end"` is copied (4 bytes). A new `String` is created from this byte array with `coder=LATIN1` (all ASCII).

11. Returns `"Log-[42]-end"`.

```
                          ┌────────────────────────────────┐
"Log-" + "[" + 42 + "]" + "-end"                           │
                          │                                │
  javac emits:            │  invokedynamic #concat         │
                          │  bootstrap: makeConcatWithConst│
                          │  recipe: "\u0001[\u0002]\u0001" │
                          │  constants: {"[", "]"}         │
                          │  dynamic: prefix, id, suffix   │
                          │                                │
  Runtime links:          │  optimal strategy              │
                          │  1. compute total len = 12     │
                          │  2. allocate byte[12]          │
                          │  3. copy Log- [4], [[1],       │
                          │     copy 42 [2], ][1],         │
                          │     copy -end [4]              │
                          │  4. new String(byte[], LATIN1) │
                          │                                │
                          ▼                                │
                    "Log-[42]-end"                         │
                          └────────────────────────────────┘
```

## 7. Gotchas & takeaways

> Indified string concatenation applies only to compile-time `+` expressions — if you build a string incrementally in a loop using `+=` on a `String` variable, each iteration still creates a new `StringBuilder` (or uses `invokedynamic`, depending on context), but the overall loop pattern is still inefficient because it allocates a new object per iteration. For loop-based string building, use an explicit `StringBuilder` (or `StringJoiner` / `String.join`).

- The `+` operator is still **safe to use everywhere** — the change is transparent. Code that was fine with `+` in JDK 8 is fine in JDK 9+, just faster. There is no need to rewrite existing `+` concatenations into `StringBuilder` for performance reasons.
- `StringBuilder` is not deprecated — it remains the right choice for complex, multi-step string construction, especially inside loops and conditionals where the concatenation shape varies per iteration and cannot be expressed as a single `+` expression.
- The `invokedynamic` approach benefits from warmup — the first few calls at a given call site may be slower (linking overhead), but after the JIT compiles the method handle, the concatenation is inlined into a tight sequence with no method-call overhead.
- Constant folding still applies — if all parts of a `+` expression are compile-time constants (e.g. `"Hello " + "World"`), the compiler folds them into a single string constant at compile time; `invokedynamic` is not involved.
- The strategy selection is based on the argument **types** at the call site, not the runtime types of the arguments — if you concatenate `Object` references, the strategy uses `String.valueOf()` internally, which may be slightly less optimal than when arguments are typed as `String` or `int`. 