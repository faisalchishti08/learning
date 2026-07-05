---
card: java
gi: 94
slug: definite-assignment-rules
title: Definite assignment rules
---

## 1. What it is

Definite assignment is a compile-time analysis that guarantees every local variable is assigned a value before it is read. The Java compiler tracks which code paths exist and whether a variable is assigned on every path that reaches a given read. If there is any path on which the variable might be unassigned, the compiler rejects the program with "variable X might not have been initialized."

```java
int x;
if (condition) {
    x = 1;
}
System.out.println(x);   // COMPILE ERROR — else branch does not assign x

int y;
if (condition) { y = 1; } else { y = 2; }
System.out.println(y);   // OK — both branches assign y
```

This check applies only to local variables and blank `final` fields. Instance fields and static fields get zero-like defaults from the JVM and are always considered assigned.

## 2. Why & when

Definite assignment prevents bugs that are common in C and C++, where reading an uninitialised stack variable produces garbage. Java eliminates this at compile time. You encounter definite assignment rules most when:
- Declaring a variable before an `if/switch` and assigning inside branches — all branches must assign.
- Using `try/catch` — the compiler analyses paths through exceptions.
- Declaring `final` instance fields — each constructor must assign every blank `final` field exactly once.

## 3. Core concept

```java
public class DefiniteAssignment {

    // ---- blank final instance field — must be assigned in constructor ----
    final int id;
    DefiniteAssignment(int id) { this.id = id; }

    public static void main(String[] args) {
        // ---- Basic: must assign before read ----
        int a;
        a = 5;            // assigned before read
        System.out.println(a);   // OK

        // ---- All branches must assign ----
        boolean flag = true;
        int b;
        if (flag) { b = 1; } else { b = 2; }
        System.out.println(b);   // OK — both branches assign

        // int c;
        // if (flag) { c = 1; }   // else branch doesn't assign
        // System.out.println(c); // COMPILE ERROR

        // ---- switch must cover all paths ----
        int day = 1;
        String name;
        switch (day) {
            case 1 -> name = "Mon";
            case 2 -> name = "Tue";
            default -> name = "Other";
        }
        System.out.println(name);  // OK — default covers all uncovered cases

        // ---- try/catch ----
        int parsed;
        try {
            parsed = Integer.parseInt("42");
        } catch (NumberFormatException e) {
            parsed = 0;   // must assign in catch too
        }
        System.out.println(parsed);  // OK

        // ---- return/throw after assignment check ----
        int val;
        if (flag) {
            val = 10;
        } else {
            throw new RuntimeException("demo");  // throw counts as assignment exit
        }
        System.out.println(val);   // OK — else throws, so val is always assigned on live paths

        // ---- loops don't guarantee assignment ----
        int loopVar;
        for (int i = 0; i < 0; i++) {   // loop may not execute
            loopVar = i;
        }
        // System.out.println(loopVar);  // COMPILE ERROR — loop might not run
    }
}
```

## 4. Diagram

<svg viewBox="0 0 700 180" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Definite assignment flow: if-else both branches assign is OK; only if branch assigns is an error; switch with default is OK; loop body may not run so no guarantee">
  <rect x="8" y="8" width="684" height="164" rx="8" fill="#0d1117"/>

  <text x="350" y="24" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Definite assignment — which paths reach the read?</text>

  <!-- if-else OK -->
  <rect x="16" y="32" width="158" height="124" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="95" y="48" fill="#6db33f" font-size="8" text-anchor="middle" font-family="monospace">if/else → OK</text>
  <text x="24" y="64" fill="#e6edf3" font-size="7.5" font-family="monospace">int x;</text>
  <text x="24" y="77" fill="#e6edf3" font-size="7.5" font-family="monospace">if(c){x=1;}</text>
  <text x="24" y="90" fill="#e6edf3" font-size="7.5" font-family="monospace">else {x=2;}</text>
  <text x="24" y="103" fill="#6db33f" font-size="7.5" font-family="monospace">print(x); // OK</text>
  <text x="24" y="120" fill="#8b949e" font-size="7" font-family="sans-serif">both paths assign</text>
  <text x="24" y="133" fill="#8b949e" font-size="7" font-family="sans-serif">→ definitely assigned</text>

  <!-- if only ERROR -->
  <rect x="184" y="32" width="158" height="124" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="263" y="48" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">if only → ERROR</text>
  <text x="192" y="64" fill="#e6edf3" font-size="7.5" font-family="monospace">int x;</text>
  <text x="192" y="77" fill="#e6edf3" font-size="7.5" font-family="monospace">if(c){x=1;}</text>
  <text x="192" y="90" fill="#8b949e" font-size="7.5" font-family="monospace">// no else</text>
  <text x="192" y="103" fill="#8b949e" font-size="7.5" font-family="monospace">print(x); // ERROR</text>
  <text x="192" y="120" fill="#8b949e" font-size="7" font-family="sans-serif">else path: unassigned</text>
  <text x="192" y="133" fill="#8b949e" font-size="7" font-family="sans-serif">→ might not be initialised</text>

  <!-- switch default OK -->
  <rect x="352" y="32" width="160" height="124" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="432" y="48" fill="#6db33f" font-size="8" text-anchor="middle" font-family="monospace">switch+default → OK</text>
  <text x="360" y="64" fill="#e6edf3" font-size="7.5" font-family="monospace">String s;</text>
  <text x="360" y="77" fill="#e6edf3" font-size="7.5" font-family="monospace">switch(n) {</text>
  <text x="360" y="90" fill="#e6edf3" font-size="7.5" font-family="monospace">  case 1 → s="a";</text>
  <text x="360" y="103" fill="#e6edf3" font-size="7.5" font-family="monospace">  default→ s="?";</text>
  <text x="360" y="116" fill="#e6edf3" font-size="7.5" font-family="monospace">}</text>
  <text x="360" y="129" fill="#6db33f" font-size="7.5" font-family="monospace">print(s); // OK</text>
  <text x="360" y="143" fill="#8b949e" font-size="7" font-family="sans-serif">default covers all</text>

  <!-- loop WARNING -->
  <rect x="522" y="32" width="158" height="124" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="601" y="48" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">loop → ERROR</text>
  <text x="530" y="64" fill="#e6edf3" font-size="7.5" font-family="monospace">int x;</text>
  <text x="530" y="77" fill="#e6edf3" font-size="7.5" font-family="monospace">while(cond) {</text>
  <text x="530" y="90" fill="#e6edf3" font-size="7.5" font-family="monospace">  x = 1;</text>
  <text x="530" y="103" fill="#e6edf3" font-size="7.5" font-family="monospace">}</text>
  <text x="530" y="116" fill="#8b949e" font-size="7.5" font-family="monospace">print(x); // ERROR</text>
  <text x="530" y="130" fill="#8b949e" font-size="7" font-family="sans-serif">loop may not execute</text>
  <text x="530" y="143" fill="#8b949e" font-size="7" font-family="sans-serif">→ not definitely assigned</text>
</svg>

The compiler checks every possible path to a read — if even one path exists where the variable might be unassigned, the code does not compile.

## 5. Runnable example

Scenario: a command-line argument parser that reads a command verb and an optional numeric argument — definite assignment rules drive the structure of the parsing code, growing from a simple if/else, to try/catch, to a switch expression that the compiler can verify exhaustively.

### Level 1 — Basic

```java
public class DefiniteAssignmentBasic {
    public static void main(String[] args) {
        // Simulate argument: "run 5" or just "run"
        String verb = "run";
        String numStr = "5";

        // The variable 'count' must be assigned before use
        int count;

        if (numStr != null && !numStr.isEmpty()) {
            count = Integer.parseInt(numStr);
        } else {
            count = 1;   // default — else branch is required
        }

        // Both branches assign count → definitely assigned → OK to read
        System.out.printf("Command: %s  Count: %d%n", verb, count);

        // Pattern: compute result depending on condition
        String message;
        boolean valid = count > 0 && count <= 100;
        if (valid) {
            message = "Executing " + count + " times";
        } else {
            message = "Count out of range: " + count;
        }
        System.out.println(message);
    }
}
```

**How to run:** `java DefiniteAssignmentBasic.java`

Without the `else { count = 1; }`, the compiler would reject `System.out.printf(... count ...)` because the `else` path — reached when `numStr` is null or empty — would leave `count` uninitialised. Adding the `else` branch satisfies definite assignment: on every path reaching the `printf`, `count` has been assigned. The same pattern applies to `message`.

### Level 2 — Intermediate

Same parser: handle parse errors with `try/catch`, and show how `throw` in a branch satisfies definite assignment.

```java
public class DefiniteAssignmentIntermediate {

    static int parseOrDefault(String s, int defaultVal) {
        int result;
        try {
            result = Integer.parseInt(s);
        } catch (NumberFormatException e) {
            result = defaultVal;   // must assign in catch; otherwise path is unassigned
        }
        return result;   // OK — both try and catch assign result
    }

    static String classify(int value) {
        String label;   // blank final local — must be assigned on all paths
        if (value < 0) {
            label = "negative";
        } else if (value == 0) {
            label = "zero";
        } else if (value < 100) {
            label = "small";
        } else {
            label = "large";   // default catch-all — every case covered
        }
        return label;   // OK
    }

    static String classifyThrow(int value) {
        String label;
        if (value < 0) {
            label = "negative";
        } else if (value == 0) {
            label = "zero";
        } else {
            // throw instead of assigning — compiler treats throw as a terminator
            throw new IllegalArgumentException("Positive values not supported");
        }
        return label;   // OK — the else throw means label is always assigned on live paths
    }

    public static void main(String[] args) {
        System.out.println(parseOrDefault("42",   -1));  // 42
        System.out.println(parseOrDefault("bad",  -1));  // -1
        System.out.println(classify(-5));                 // negative
        System.out.println(classify(50));                 // small
        System.out.println(classify(200));                // large

        try {
            System.out.println(classifyThrow(5));
        } catch (IllegalArgumentException e) {
            System.out.println("Caught: " + e.getMessage());
        }
    }
}
```

**How to run:** `java DefiniteAssignmentIntermediate.java`

In `parseOrDefault`, the `catch` block assigns `result = defaultVal`. Without it, the catch path would leave `result` unassigned before `return result`. In `classify`, the final `else` branch is the key — without it, the compiler cannot know that every integer is covered, so `label` would not be definitely assigned. In `classifyThrow`, the `else { throw ... }` branch terminates (throws always terminate control flow), so the compiler considers `label` definitely assigned on all remaining live paths.

### Level 3 — Advanced

Same parser: use a `switch` expression (Java 14+) that the compiler can verify exhaustively, blank `final` fields with multiple constructors, and a loop-then-read pattern that requires initialisation before the loop.

```java
import java.util.*;

public class DefiniteAssignmentAdvanced {

    record Command(String verb, int count, String mode) {
        // blank final fields are implicit in records — assigned in canonical constructor

        static Command parse(String input) {
            String[] parts = input.trim().split("\\s+");
            if (parts.length < 1 || parts[0].isEmpty())
                throw new IllegalArgumentException("Empty command");

            String verb = parts[0];
            int    count = parts.length >= 2 ? Integer.parseInt(parts[1]) : 1;
            // switch expression — exhaustive (enum-based or with default)
            String mode = switch (verb) {
                case "run"    -> "execute";
                case "dry-run"-> "simulate";
                case "check"  -> "validate";
                default       -> "unknown";
            };

            return new Command(verb, count, mode);
        }
    }

    public static void main(String[] args) {
        String[] inputs = {"run 3", "dry-run", "check 10", "unknown-verb 1"};

        for (String input : inputs) {
            Command cmd = Command.parse(input);
            System.out.printf("%-16s → verb=%-12s count=%2d  mode=%s%n",
                input, cmd.verb(), cmd.count(), cmd.mode());
        }

        // Loop followed by read — must initialise BEFORE the loop
        List<Integer> numbers = List.of(3, 7, 2, 9, 1);
        int max = Integer.MIN_VALUE;   // initialise before loop — not inside it
        for (int n : numbers) {
            if (n > max) max = n;
        }
        System.out.println("Max: " + max);   // OK — max assigned before loop

        // Without the pre-loop initialisation, max would be unassigned
        // if numbers were empty — the compiler rejects int max; inside the loop.

        // Blank final in anonymous scenario
        final int threshold;
        boolean premium = true;
        if (premium) {
            threshold = 1000;
        } else {
            threshold = 500;
        }
        System.out.println("Threshold: " + threshold);
    }
}
```

**How to run:** `java DefiniteAssignmentAdvanced.java`

The `switch` expression with `default -> "unknown"` is exhaustive — every possible `String` value is handled. The compiler verifies that `mode` is definitely assigned by the switch expression. `max = Integer.MIN_VALUE` before the loop is mandatory because the enhanced `for` loop might not execute at all (if `numbers` were empty), leaving `max` unassigned. The blank `final int threshold` is assigned in both branches of the `if/else`, satisfying definite assignment for `final` locals.

## 6. Walkthrough

Execution trace through `DefiniteAssignmentAdvanced.main`:

**`Command.parse("dry-run")`.** `parts = ["dry-run"]`, so `parts.length = 1`. `verb = "dry-run"`. `count = 1` (the `parts.length >= 2` check is false). The `switch` expression evaluates `verb = "dry-run"`: matches `case "dry-run"` → `mode = "simulate"`. The compiler was satisfied at compile time that every `switch` arm assigns `mode` — so `mode` is definitely assigned after the switch expression.

**Max loop.** `max = Integer.MIN_VALUE` (-2 147 483 648). Iteration: `n=3 > max` → `max=3`. `n=7 > 3` → `max=7`. `n=2 < 7` → unchanged. `n=9 > 7` → `max=9`. `n=1 < 9` → unchanged. Final `max=9`. If the list were empty, `max` would remain `Integer.MIN_VALUE` — which is a valid (if unexpected) sentinel value, but the compiler would not let us read a `max` that might be genuinely unassigned.

**Blank final `threshold`.** The compiler analyses the `if/else` and confirms: the `if` branch assigns `threshold = 1000`, and the `else` branch assigns `threshold = 500`. There is no path that bypasses both branches. Therefore `threshold` is definitely assigned before `println`.

```
Definite assignment analysis for switch:
  String mode;
  switch (verb) {
    case "run"     → mode = "execute";    ← assigns
    case "dry-run" → mode = "simulate";   ← assigns
    case "check"   → mode = "validate";   ← assigns
    default        → mode = "unknown";    ← assigns
  }
  // Every arm assigns mode → definitely assigned after switch
  return new Command(verb, count, mode);  // OK
```

## 7. Gotchas & takeaways

> **A loop body does not satisfy definite assignment for variables declared outside the loop.** Even if the loop always runs at least once at runtime, the compiler cannot prove this statically. Initialise variables to a sensible default before the loop, or restructure the code so the variable is declared inside the loop.

> **`throw` and `return` are control-flow terminators — they satisfy definite assignment for the current path.** A branch ending in `throw new IllegalArgumentException(...)` or `return` does not need to assign a variable, because that path never reaches the subsequent read.

- Definite assignment is a compile-time check — it prevents reading local variables that might be uninitialised.
- All branches of `if/else` and all arms of `switch` (including `default`) must assign the variable for it to be definitely assigned afterwards.
- `throw` and `return` terminate the path and count as "never reaches the read," satisfying definite assignment on the remaining paths.
- `try/catch`: the variable must be assigned in both the `try` body and every `catch` block if it is read after the `try/catch`.
- Instance and static fields always have zero-like defaults — they are always considered assigned and are not subject to this rule.
- The `switch` expression (Java 14+) can be exhaustive by the compiler's analysis — use `default` to cover remaining cases and satisfy definite assignment.
