---
card: java
gi: 89
slug: local-variables
title: Local variables
---

## 1. What it is

A local variable is declared inside a method, constructor, or initializer block. It exists only within the enclosing block `{ }` and is destroyed when execution leaves that block. Unlike instance and static fields, local variables have **no automatic default value** — the compiler requires every local variable to be definitely assigned before it is read.

```java
void process() {
    int count = 0;         // local variable — exists for the life of this method
    String label;          // declared but not yet assigned
    label = "hello";       // assigned before first use

    if (true) {
        int inner = 5;     // exists only inside this if-block
    }
    // inner is not accessible here — out of scope
}
```

## 2. Why & when

Local variables are the workhorse of method logic. Key properties:
- **No default** — the compiler enforces initialization before use, preventing undetected use of garbage values.
- **Scope-limited** — they live exactly as long as they are needed, reducing accidental sharing of state between unrelated code paths.
- **Stack-allocated** — (at the JVM level) local variables typically reside on the call stack, which is faster to allocate and deallocate than heap memory.
- **Thread-private** — each thread call stack has its own copy of local variables, so they are inherently thread-safe.

Use `final` (or effectively-final) locals whenever the value should not change — this also enables lambda and inner-class capture.

## 3. Core concept

```java
public class LocalVariables {
    public static void main(String[] args) {
        // ---- Definite assignment ----
        int a;
        // System.out.println(a);  // compile error: a might not have been initialized
        a = 10;
        System.out.println(a);   // 10 — OK after assignment

        // ---- Block scope ----
        {
            int inner = 42;
            System.out.println(inner);  // 42 — accessible here
        }
        // System.out.println(inner);   // compile error — out of scope

        // ---- Loop variables ----
        for (int i = 0; i < 3; i++) {
            int doubled = i * 2;        // new doubled variable each iteration
            System.out.println(doubled);
        }
        // i and doubled are not accessible here

        // ---- var (type inference, Java 10+) ----
        var msg  = "Hello";            // String
        var nums = new int[]{1, 2, 3}; // int[]
        System.out.println(msg.toUpperCase());

        // ---- final local ----
        final int MAX = 100;
        // MAX = 200;  // compile error

        // ---- Effectively final — captured by lambda ----
        String prefix = "item-";  // not declared final, but never reassigned
        var list = java.util.List.of("a", "b", "c");
        list.forEach(s -> System.out.println(prefix + s)); // prefix is effectively final

        // ---- Conditional definite assignment ----
        int value;
        boolean condition = true;
        if (condition) {
            value = 1;
        } else {
            value = 2;
        }
        System.out.println(value);  // OK — both branches assign value

        // ---- Not definitely assigned ----
        int maybe;
        if (condition) {
            maybe = 1;
        }
        // System.out.println(maybe);  // compile error — else branch doesn't assign
    }
}
```

## 4. Diagram

<svg viewBox="0 0 700 175" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Local variable scope: method scope, inner block scope, loop variable scope, showing how each block creates a new scope layer">
  <rect x="8" y="8" width="684" height="159" rx="8" fill="#0d1117"/>

  <!-- outer method scope -->
  <rect x="16" y="18" width="668" height="133" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="26" y="34" fill="#6db33f" font-size="8" font-family="monospace">void method() {</text>
  <text x="40" y="48" fill="#e6edf3" font-size="8" font-family="monospace">int count = 0;    ← method scope</text>
  <text x="40" y="62" fill="#e6edf3" font-size="8" font-family="monospace">String msg;       ← declared, not yet assigned</text>

  <!-- inner if block -->
  <rect x="40" y="68" width="360" height="50" rx="4" fill="#0d1117" stroke="#79c0ff" stroke-width="1"/>
  <text x="50" y="83" fill="#79c0ff" font-size="8" font-family="monospace">if (x &gt; 0) {</text>
  <text x="64" y="97" fill="#e6edf3" font-size="8" font-family="monospace">int inner = 5;  ← exists only here</text>
  <text x="50" y="111" fill="#79c0ff" font-size="8" font-family="monospace">}  ← inner dies here</text>

  <!-- for loop scope -->
  <rect x="416" y="68" width="256" height="50" rx="4" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="426" y="83" fill="#8b949e" font-size="8" font-family="monospace">for (int i=0; ..) {</text>
  <text x="440" y="97" fill="#e6edf3" font-size="8" font-family="monospace">int step = i*2;</text>
  <text x="426" y="111" fill="#8b949e" font-size="8" font-family="monospace">}  ← i, step die here</text>

  <text x="40" y="132" fill="#e6edf3" font-size="8" font-family="monospace">msg = "hi";  ← assigned; now usable</text>
  <text x="40" y="145" fill="#8b949e" font-size="8" font-family="monospace">// inner, i, step not visible here</text>
  <text x="670" y="145" fill="#8b949e" font-size="8" text-anchor="end" font-family="monospace">}</text>
</svg>

Each `{ }` block creates a new scope layer; variables declared inside a block are destroyed on exit and are not accessible outside — the compiler enforces this.

## 5. Runnable example

Scenario: a text-stats analyser that counts words, sentences, and characters in a passage — variables are declared at the tightest scope possible, illustrating proper local-variable discipline. The example grows from basic counters, to accumulating per-word statistics, to a full report using effectively-final captured variables.

### Level 1 — Basic

```java
public class LocalVarsBasic {
    public static void main(String[] args) {
        String passage = "The quick brown fox jumps over the lazy dog. "
                       + "Pack my box with five dozen liquor jugs.";

        int charCount  = 0;
        int wordCount  = 0;
        int spaceCount = 0;

        for (int i = 0; i < passage.length(); i++) {
            char c = passage.charAt(i);   // c is local to this for body
            charCount++;
            if (c == ' ')  spaceCount++;
        }

        // wordCount via split — local var used only in this block
        String[] words = passage.split("\\s+");
        wordCount = words.length;

        System.out.println("=== Text stats ===");
        System.out.printf("Characters : %d%n", charCount);
        System.out.printf("Words      : %d%n", wordCount);
        System.out.printf("Spaces     : %d%n", spaceCount);

        // words is still accessible here but no longer needed
    }
}
```

**How to run:** `java LocalVarsBasic.java`

`char c` is declared inside the `for` loop body — it is created on each iteration and destroyed at the end of each iteration. `String[] words` is declared just before it is first needed, minimising the scope over which it is live. Keeping variables close to their first use makes code easier to read and helps the JVM's optimiser.

### Level 2 — Intermediate

Same analyser: track per-sentence statistics using variables declared inside a loop body, and demonstrate that a `final` loop counter cannot be incremented — use an index variable instead.

```java
public class LocalVarsIntermediate {
    public static void main(String[] args) {
        String passage = "First sentence here. Second one follows. Third ends it.";
        String[] sentences = passage.split("\\. *");

        System.out.printf("%-8s  %-5s  %-10s  %s%n",
            "Sentence", "Words", "AvgWordLen", "Text");
        System.out.println("-".repeat(56));

        int totalWords = 0;   // accumulator — declared in method scope

        for (int idx = 0; idx < sentences.length; idx++) {
            // These are new local vars each iteration
            String sent  = sentences[idx].trim();
            String[] ws  = sent.split("\\s+");
            int     wc   = ws.length;
            double  avg  = 0.0;

            // Compute average word length
            int charSum = 0;
            for (String w : ws) {
                charSum += w.length();
            }
            avg = wc > 0 ? (double) charSum / wc : 0.0;

            totalWords += wc;

            System.out.printf("  #%-5d  %-5d  %10.2f  %s%n",
                idx + 1, wc, avg, sent);
        }

        System.out.printf("%nTotal words across all sentences: %d%n", totalWords);

        // Definite assignment in conditional
        String summary;
        if (totalWords < 10) {
            summary = "short";
        } else if (totalWords < 20) {
            summary = "medium";
        } else {
            summary = "long";
        }
        System.out.println("Passage length: " + summary);
    }
}
```

**How to run:** `java LocalVarsIntermediate.java`

`sent`, `ws`, `wc`, `avg`, and `charSum` are all declared inside the outer `for` loop body — they are re-created on every iteration. This means a bug in iteration N cannot accidentally affect iteration N+1 through stale state. `summary` is declared before the `if/else if/else` chain; the compiler accepts the read after the chain because every branch assigns `summary`, satisfying the definite-assignment rule.

### Level 3 — Advanced

Same analyser: use effectively-final local variables to pass context into a stream pipeline and demonstrate the capture rule that prevents mutation of locals inside lambdas.

```java
import java.util.*;
import java.util.stream.*;

public class LocalVarsAdvanced {

    record WordStats(String word, int length, int occurrences) {}

    public static void main(String[] args) {
        String passage = "to be or not to be that is the question whether "
                       + "tis nobler in the mind to suffer the slings";

        String[] tokens = passage.split("\\s+");

        // Effectively final — used in lambda below
        int totalTokens = tokens.length;

        // Build frequency map
        var freq = new TreeMap<String, Integer>();
        for (String t : tokens) {
            freq.merge(t, 1, Integer::sum);
        }

        // totalTokens is effectively final — not reassigned after this point
        var stats = freq.entrySet().stream()
            .map(e -> new WordStats(e.getKey(), e.getKey().length(), e.getValue()))
            .sorted(Comparator.comparingInt(WordStats::occurrences).reversed())
            .collect(Collectors.toList());

        System.out.printf("%-12s  %6s  %11s  %s%n",
            "Word", "Len", "Count", "Freq%");
        System.out.println("-".repeat(42));

        for (var ws : stats) {
            // ws is new each iteration — fresh local variable
            double freqPct = 100.0 * ws.occurrences() / totalTokens; // capture OK
            System.out.printf("%-12s  %6d  %11d  %5.1f%%%n",
                ws.word(), ws.length(), ws.occurrences(), freqPct);
        }

        // Lambda capture rule demo
        int multiplier = 2;           // effectively final
        List<Integer> lengths = Arrays.stream(tokens)
            .map(t -> t.length() * multiplier)  // captures multiplier — OK
            .collect(Collectors.toList());
        System.out.println("\nFirst 5 doubled lengths: " + lengths.subList(0, 5));

        // multiplier = 3;  // un-commenting this makes 'multiplier' no longer
                             // effectively final → compile error in the lambda above
    }
}
```

**How to run:** `java LocalVarsAdvanced.java`

`totalTokens` is effectively final because it is assigned exactly once and never reassigned. Lambdas and anonymous classes can capture effectively-final local variables (no `final` keyword required since Java 8 — the compiler checks automatically). If `multiplier = 3` were added after the lambda, `multiplier` would no longer be effectively final and the lambda would fail to compile. Each `var ws` in the enhanced `for` loop is a fresh local variable per iteration, so `freqPct` computed from `ws` is always per-word without any stale state.

## 6. Walkthrough

Execution trace through `LocalVarsAdvanced.main`:

**Tokenisation.** `passage.split("\\s+")` produces a `String[]` of 18 tokens. `tokens` is a local reference variable pointing to this array. `int totalTokens = 18` is stored on the call stack.

**Frequency map.** The `for (String t : tokens)` loop iterates over each token. `t` is a new local reference each iteration. `freq.merge(t, 1, Integer::sum)` inserts `1` for new keys or increments existing ones. After the loop, `freq` contains each unique word and its count.

**Stream pipeline.** `freq.entrySet().stream()` starts a stream over the map entries. `.map(e -> new WordStats(...))` creates a `WordStats` record per entry. `.sorted(...)` sorts by occurrence count descending. `.collect(Collectors.toList())` materialises the stream into a `List<WordStats>`. The variable `stats` is then a local reference to this list.

**Output loop.** For each `var ws : stats`, `freqPct` is computed fresh from `ws.occurrences()` and the captured `totalTokens`. The capture of `totalTokens` in the lambda above is valid because `totalTokens` was never reassigned after its first assignment.

```
Local variable lifetime:
  tokens         → lives for entire method
  totalTokens    → lives for entire method, effectively final
  freq           → lives for entire method
  t (loop var)   → lives for one iteration of for-each loop
  stats          → lives from assignment to end of method
  ws (loop var)  → lives for one iteration of enhanced for
  freqPct        → lives for one iteration of enhanced for
```

## 7. Gotchas & takeaways

> **Local variables captured by lambdas or inner classes must be effectively final.** If you reassign a local variable after a lambda captures it, the code will not compile. The fix is either to not reassign the variable, or to copy the value into a new final local before the lambda.

> **A variable declared in a `for` initialiser is scoped to the loop — it is not accessible after the loop.** This is often useful (the index variable `i` does not pollute the enclosing scope), but can surprise developers who expect the loop variable to be available after the loop ends.

- Local variables have no default value; the compiler enforces definite assignment before first read.
- Scope is determined by the enclosing `{ }` block; a variable declared in an inner block is inaccessible after that block closes.
- Declare variables at the smallest scope that is sufficient — close to first use, not at the top of the method.
- `final` (or effectively-final) locals can be captured by lambdas and anonymous inner classes.
- `var` infers the type at compile time and is valid only for local variable declarations with an initializer.
- Loop variables (both `for` index and enhanced-for element) are scoped to the loop body.
