# Java Control Flow

## Overview

Control flow determines the order in which statements execute. Without it, programs run line by line top to bottom — not very useful. Java provides conditionals (if/switch) to branch, and loops (for/while/do-while) to repeat. Understanding the subtleties (fall-through, short-circuit, labeled breaks) prevents hard-to-find bugs.

---

## 1. if / else if / else

### What is it

The most fundamental branching construct. Evaluates a boolean expression and executes one of two blocks.

### Visual Diagram

```
if (condition) {
    ┌──────────────────┐
    │  execute if TRUE │
    └──────────────────┘
} else if (other) {
    ┌──────────────────────────┐
    │  execute if other TRUE   │
    └──────────────────────────┘
} else {
    ┌──────────────────────────────────┐
    │  execute if all conditions FALSE │
    └──────────────────────────────────┘
}

Flow:
  condition? ──YES──► block1 ──►
      │
     NO
      │
  other? ────YES──► block2 ──►
      │
     NO
      │
      ▼
  else block ──────────────────►
```

### Example 1 — Basic if/else

```java
public class IfElse {
    public static void main(String[] args) {
        int score = 85;

        if (score >= 90) {
            System.out.println("Grade: A");
        } else if (score >= 80) {
            System.out.println("Grade: B");  // ← this executes
        } else if (score >= 70) {
            System.out.println("Grade: C");
        } else {
            System.out.println("Grade: F");
        }
    }
}
```

**What this does:** Evaluates conditions top to bottom. Once a true condition is found, its block executes and the rest are skipped. Only one branch executes.

### Example 2 — Nested if

```java
public class NestedIf {
    public static void main(String[] args) {
        int age = 20;
        boolean hasLicense = true;

        if (age >= 18) {
            if (hasLicense) {
                System.out.println("Can drive");        // ← this
            } else {
                System.out.println("Too young for license but old enough");
            }
        } else {
            System.out.println("Too young");
        }

        // Equivalent with &&  (prefer this — less nesting)
        if (age >= 18 && hasLicense) {
            System.out.println("Can drive");
        }
    }
}
```

**What this does:** Nested ifs work but increase complexity. When conditions are independent AND requirements, using `&&` is cleaner. Reduce nesting whenever possible.

### Dry Run — Multi-Condition Evaluation

```java
int x = 15;
if (x > 10 && x < 20 && x % 3 == 0) {
    System.out.println("match");
}
```

| Step | Sub-expression | Value | Short-circuit? |
|------|----------------|-------|----------------|
| 1    | `x > 10`       | `15 > 10` → true  | continue |
| 2    | `x < 20`       | `15 < 20` → true  | continue |
| 3    | `x % 3 == 0`   | `15 % 3 = 0 → 0 == 0` → true | —   |
| 4    | All true → enter block | prints "match" | — |

If step 1 were false (e.g. x=5), steps 2 and 3 would never execute.

### Example 3 — Dangling else Pitfall

```java
public class DanglingElse {
    public static void main(String[] args) {
        int x = 0;
        int y = 1;

        // Where does the else belong?
        if (x > 0)
            if (y > 0)
                System.out.println("both positive");
        else               // ← this else belongs to the INNER if (closest if)!
            System.out.println("x positive but y not");

        // This doesn't print "x <= 0" even when x=0!
        // The else is paired with (if y > 0), not (if x > 0)

        // Fix: always use braces
        if (x > 0) {
            if (y > 0) {
                System.out.println("both positive");
            }
        } else {
            System.out.println("x not positive"); // ← now correctly paired
        }
    }
}
```

**What this does:** The "dangling else" problem — without braces, `else` binds to the nearest `if`. Always use curly braces `{}` to be explicit.

> ⚠️ **Pitfall:** Always use braces in if/else, even for single-line bodies. Without them, adding a second statement under the if won't be part of the if block.

---

## 2. Classic switch

### What is it

Switch tests a single variable against multiple constant values. More readable than a chain of `if/else if` when matching against a fixed set of values.

### Visual Diagram — Fall-Through Behavior

```
switch (value) {
    case A: ──► executes ──► falls through to case B! (no break)
    case B: ──► executes ──► falls through to case C! (no break)
    case C: ──► executes ──► break ──► exits switch
    default:──► executes if no case matches
}

With break:
    case A: ──► executes ──► break ──► exits (skips B, C, default)
```

### Example 1 — Classic switch with Fall-Through

```java
public class ClassicSwitch {
    public static void main(String[] args) {
        int day = 3;
        String type;

        switch (day) {
            case 1:
            case 2:
            case 3:
            case 4:
            case 5:
                type = "Weekday";   // cases 1-5 all fall through to here
                break;
            case 6:
            case 7:
                type = "Weekend";
                break;
            default:
                type = "Invalid";
        }
        System.out.println(type); // Weekday
    }
}
```

**What this does:** Cases 1 through 5 fall through to the same assignment. This is intentional — it's how you group multiple values in a classic switch. The `break` at the end of each group stops fall-through.

### Example 2 — Missing break (Bug!)

```java
public class FallThroughBug {
    public static void main(String[] args) {
        int x = 2;
        switch (x) {
            case 1:
                System.out.println("one");
                break;
            case 2:
                System.out.println("two");    // ← executes
                // MISSING BREAK!
            case 3:
                System.out.println("three");  // ← also executes! (bug)
                break;
            case 4:
                System.out.println("four");
        }
        // Prints: two
        //         three
    }
}
```

**What this does:** Missing `break` causes execution to fall through into the next case. This is almost always a bug. Classic switch's fall-through is a known Java design mistake.

### Example 3 — Switch on String (Java 7+)

```java
public class StringSwitch {
    public static void main(String[] args) {
        String command = "START";

        switch (command) {
            case "START":
                System.out.println("Starting...");
                break;
            case "STOP":
                System.out.println("Stopping...");
                break;
            case "PAUSE":
                System.out.println("Pausing...");
                break;
            default:
                System.out.println("Unknown command: " + command);
        }
        // Prints: Starting...
    }
}
```

**What this does:** Switch on String uses `.equals()` internally (plus `hashCode()` optimization). Null value in switch variable throws NullPointerException. Case values must be compile-time constants.

### Switch works with: `byte`, `short`, `int`, `char`, `String` (Java 7+), `enum`

> ⚠️ **Pitfall:** `switch(null)` throws `NullPointerException`. Always null-check before switching on a String or enum.

---

## 3. Enhanced Switch Expression [Java 14+]

### What is it

A modern, cleaner switch that eliminates fall-through, allows switch as an expression (returns a value), and uses arrow (`->`) syntax. No `break` needed with arrows.

### Visual Diagram — Arrow vs Classic

```
Classic (fall-through risk):           Enhanced (no fall-through):
switch (x) {                           int result = switch (x) {
  case A:                                case A -> valueA;
    // code                              case B, C -> valueBC;
    break;                               default -> defaultValue;
  case B:                              };
    // code
    break;
}
```

### Example 1 — Switch Expression with Arrow Syntax

```java
public class SwitchExpression {
    public static void main(String[] args) {
        int day = 3;

        // Switch as expression — returns a value
        String dayName = switch (day) {
            case 1 -> "Monday";
            case 2 -> "Tuesday";
            case 3 -> "Wednesday";
            case 4 -> "Thursday";
            case 5 -> "Friday";
            case 6 -> "Saturday";
            case 7 -> "Sunday";
            default -> throw new IllegalArgumentException("Invalid: " + day);
        };

        System.out.println(dayName); // Wednesday
    }
}
```

**What this does:** Arrow syntax (`->`) means no fall-through. Each case is independent. The switch returns a value directly — cleaner than assigning inside each case. `default` must cover all cases when used as expression.

### Example 2 — Multiple Values per Case

```java
public class MultiCaseSwitch {
    public static void main(String[] args) {
        int month = 4; // April

        int daysInMonth = switch (month) {
            case 1, 3, 5, 7, 8, 10, 12 -> 31;
            case 4, 6, 9, 11            -> 30;
            case 2                      -> 28; // ignoring leap year
            default -> throw new IllegalArgumentException("Invalid month");
        };

        System.out.println("Days in April: " + daysInMonth); // 30
    }
}
```

**What this does:** Multiple values in one case separated by commas. Much cleaner than fall-through for this pattern.

### Example 3 — yield for Multi-Statement Cases

```java
public class SwitchYield {
    public static void main(String[] args) {
        int x = 5;

        String result = switch (x) {
            case 1, 2, 3 -> "small";
            case 4, 5, 6 -> {
                // Multi-statement block — must use yield to produce value
                String desc = x % 2 == 0 ? "even" : "odd";
                yield "medium-" + desc;   // yield is the return statement for switch blocks
            }
            default -> "large";
        };

        System.out.println(result); // medium-odd
    }
}
```

**What this does:** When you need multiple statements in a switch case, use a block `{}` with `yield` to return the value. `yield` is like `return` but for switch expressions.

### Example 4 — Switch with Enum (exhaustive)

```java
public class SwitchEnum {
    enum Season { SPRING, SUMMER, FALL, WINTER }

    public static void main(String[] args) {
        Season s = Season.SUMMER;

        String description = switch (s) {
            case SPRING -> "Warm and rainy";
            case SUMMER -> "Hot and sunny";
            case FALL   -> "Cool and windy";
            case WINTER -> "Cold and snowy";
            // No default needed — all enum cases covered (exhaustive)
        };

        System.out.println(description); // Hot and sunny
    }
}
```

**What this does:** When switching on enum, if all constants are covered, `default` is not required. Compiler verifies exhaustiveness.

---

## 4. for Loop

### What is it

Repeats a block of code. The `for` loop is ideal when you know in advance how many times to iterate. It has three parts: initialization, condition, and update.

### Visual Diagram

```
for (init; condition; update) {
    body
}

Execution flow:
  ┌─ init (runs once)
  │
  ▼
  condition? ──FALSE──► exit loop
      │
     TRUE
      │
  ▼
  body executes
      │
  update
      │
  ▲ (back to condition check)
```

### Example 1 — Basic for Loop

```java
public class ForLoop {
    public static void main(String[] args) {
        // Classic counting loop
        for (int i = 0; i < 5; i++) {
            System.out.print(i + " ");  // 0 1 2 3 4
        }
        System.out.println();

        // Count backwards
        for (int i = 5; i >= 1; i--) {
            System.out.print(i + " ");  // 5 4 3 2 1
        }
        System.out.println();

        // Step by 2
        for (int i = 0; i <= 10; i += 2) {
            System.out.print(i + " ");  // 0 2 4 6 8 10
        }
    }
}
```

**What this does:** The loop variable `i` is declared in the init section — its scope is limited to the loop. The condition is checked before each iteration (including the first).

### Dry Run — for Loop Iteration Trace

```java
int sum = 0;
for (int i = 1; i <= 4; i++) {
    sum += i;
}
```

| Iteration | i (before check) | Condition `i<=4` | Body: `sum += i` | i after update |
|-----------|-------------------|-------------------|-------------------|----------------|
| Start     | `i=1`             | 1<=4 → true       | sum = 0+1 = 1     | i=2            |
| 2nd       | `i=2`             | 2<=4 → true       | sum = 1+2 = 3     | i=3            |
| 3rd       | `i=3`             | 3<=4 → true       | sum = 3+3 = 6     | i=4            |
| 4th       | `i=4`             | 4<=4 → true       | sum = 6+4 = 10    | i=5            |
| Exit      | `i=5`             | 5<=4 → **false**  | — (loop ends)     | —              |

Final value: `sum = 10`

### Example 2 — Nested for Loops

```java
public class NestedFor {
    public static void main(String[] args) {
        // Multiplication table
        for (int i = 1; i <= 3; i++) {
            for (int j = 1; j <= 3; j++) {
                System.out.printf("%3d", i * j);
            }
            System.out.println();
        }
        // Output:
        //   1  2  3
        //   2  4  6
        //   3  6  9
    }
}
```

**What this does:** Inner loop completes fully for each iteration of the outer loop. Total iterations = outer × inner = 3 × 3 = 9.

### Example 3 — Multiple Variables in for Loop

```java
public class MultiVarFor {
    public static void main(String[] args) {
        // Two variables in init, two updates
        for (int i = 0, j = 10; i < j; i++, j--) {
            System.out.println("i=" + i + " j=" + j);
        }
        // i=0 j=10
        // i=1 j=9
        // i=2 j=8
        // i=3 j=7
        // i=4 j=6
        // (stops when i=5 j=5, condition i<j is false)
    }
}
```

**What this does:** Multiple variables can be declared in the init section (same type only). Multiple update expressions separated by comma. Runs until condition fails (when i and j meet in the middle).

---

## 5. Enhanced for-each Loop

### What is it

The for-each loop iterates over every element in an array or collection without managing an index. Cleaner and less error-prone than index-based loops.

### Example 1 — Iterating Arrays

```java
public class ForEachArray {
    public static void main(String[] args) {
        int[] numbers = {5, 3, 8, 1, 9, 2};

        // For-each: no index needed
        int sum = 0;
        for (int n : numbers) {
            sum += n;
        }
        System.out.println("Sum: " + sum); // 28

        // 2D array
        int[][] matrix = {{1,2}, {3,4}, {5,6}};
        for (int[] row : matrix) {
            for (int val : row) {
                System.out.print(val + " ");
            }
        }
        // 1 2 3 4 5 6
    }
}
```

**What this does:** For-each reads "for each element in the collection". The loop variable `n` gets a copy of each element. Clean syntax, no off-by-one errors.

### Example 2 — Iterating Collections

```java
import java.util.*;

public class ForEachCollection {
    public static void main(String[] args) {
        List<String> names = List.of("Alice", "Bob", "Charlie");

        for (String name : names) {
            System.out.println("Hello, " + name + "!");
        }

        Map<String, Integer> scores = new HashMap<>();
        scores.put("Alice", 95);
        scores.put("Bob", 87);

        for (Map.Entry<String, Integer> entry : scores.entrySet()) {
            System.out.println(entry.getKey() + ": " + entry.getValue());
        }
    }
}
```

**What this does:** For-each works with any `Iterable` — List, Set, Map.entrySet(), etc. This is the preferred way to iterate collections when you don't need the index.

### Example 3 — What For-Each Can't Do

```java
import java.util.*;

public class ForEachLimits {
    public static void main(String[] args) {
        int[] arr = {1, 2, 3, 4, 5};

        // CAN'T modify original array elements via for-each
        for (int n : arr) {
            n = n * 2;  // only modifies LOCAL copy, not arr[i]!
        }
        System.out.println(arr[0]); // still 1

        // For modifications, use index-based loop:
        for (int i = 0; i < arr.length; i++) {
            arr[i] = arr[i] * 2;  // modifies original
        }
        System.out.println(arr[0]); // 2

        // CAN'T remove from List during for-each iteration:
        List<String> list = new ArrayList<>(List.of("a", "b", "c"));
        // This throws ConcurrentModificationException:
        // for (String s : list) { if (s.equals("b")) list.remove(s); }

        // Safe removal: use Iterator
        Iterator<String> it = list.iterator();
        while (it.hasNext()) {
            if (it.next().equals("b")) it.remove(); // safe!
        }
        System.out.println(list); // [a, c]
    }
}
```

**What this does:** For-each gives you a copy of each primitive element, so modifying `n` doesn't change the array. Also, modifying the collection during iteration causes `ConcurrentModificationException`. Use `Iterator.remove()` for safe removal.

> ⚠️ **Pitfall:** Never modify a collection you're iterating with for-each. Use `Iterator.remove()`, `removeIf()`, or collect to a new list.

---

## 6. while and do-while Loops

### What is it

`while` repeats while a condition is true. `do-while` is the same but guarantees the body executes **at least once** (checks condition at the end).

### Visual Diagram

```
while loop:                    do-while loop:
                               ┌──────────────┐
condition? ─TRUE──► body       │ body executes│  ← always runs once
    ▲           │              └──────────────┘
    └───────────┘                     │
    condition? ─FALSE──► exit    condition? ─TRUE──► back to body
                                  condition? ─FALSE──► exit
```

### Example 1 — while Loop

```java
public class WhileLoop {
    public static void main(String[] args) {
        // Process until sentinel value
        int[] data = {3, 7, 2, 0, 5, 9};
        int i = 0;
        int sum = 0;

        while (i < data.length && data[i] != 0) {
            sum += data[i];
            i++;
        }
        System.out.println("Sum before 0: " + sum); // 12 (3+7+2)

        // Countdown
        int count = 3;
        while (count > 0) {
            System.out.println("T-" + count);
            count--;
        }
        System.out.println("Launch!");
    }
}
```

**What this does:** `while` is best when you don't know how many iterations you need — just a stopping condition. The condition is checked before each iteration.

### Example 2 — do-while Loop

```java
import java.util.Scanner;

public class DoWhile {
    public static void main(String[] args) {
        // Classic use: input validation (always ask at least once)
        // Simulating with predetermined values for demo:
        int[] inputs = {-5, 0, 42};  // pretend user enters these
        int idx = 0;
        int value;

        do {
            value = inputs[idx++];
            System.out.println("Got: " + value);
        } while (value <= 0);  // keep asking until positive

        System.out.println("Accepted: " + value); // 42

        // do-while executes at least once even if condition is false from start:
        do {
            System.out.println("This prints exactly once");
        } while (false);
    }
}
```

**What this does:** `do-while` is perfect for "at least once" scenarios like input validation — always ask at least once, then repeat if invalid. The condition is checked AFTER the body executes.

### Dry Run — while Loop Trace

```java
int n = 1;
int product = 1;
while (n <= 4) {
    product *= n;
    n++;
}
```

| Iteration | n (start) | Condition `n<=4` | Body: `product *= n` | n (end) |
|-----------|-----------|-------------------|----------------------|---------|
| 1st       | 1         | 1<=4 → true       | product = 1*1 = 1    | 2       |
| 2nd       | 2         | 2<=4 → true       | product = 1*2 = 2    | 3       |
| 3rd       | 3         | 3<=4 → true       | product = 2*3 = 6    | 4       |
| 4th       | 4         | 4<=4 → true       | product = 6*4 = 24   | 5       |
| Exit      | 5         | 5<=4 → **false**  | —                    | —       |

Final: `product = 24` (which is 4!)

### Example 3 — Infinite Loop with break

```java
public class InfiniteLoop {
    public static void main(String[] args) {
        int x = 1;

        while (true) {  // infinite loop
            System.out.println(x);
            x *= 2;
            if (x > 100) break;  // exit condition inside loop
        }
        // Prints: 1 2 4 8 16 32 64 128
    }
}
```

**What this does:** Sometimes the exit condition is more naturally expressed inside the loop than at the top. `while(true)` with `break` is a common and accepted pattern for this.

---

## 7. break, continue, and Labeled Statements

### What is it

- **`break`** — exits the innermost loop (or switch) immediately
- **`continue`** — skips the rest of the current iteration and goes to next
- **Labeled break/continue** — break/continue to a specific outer loop

### Visual Diagram — break vs continue

```
for (...) {
    statements before;
    if (condition) break;    ─────────────────► exits loop entirely
    if (condition) continue; ──► skips to update/condition, next iteration
    statements after;
}
```

### Example 1 — break

```java
public class BreakDemo {
    public static void main(String[] args) {
        // Find first number divisible by 7
        int found = -1;
        for (int i = 1; i <= 100; i++) {
            if (i % 7 == 0) {
                found = i;
                break;  // exit loop as soon as found
            }
        }
        System.out.println("First multiple of 7: " + found); // 7

        // Search in 2D array
        int[][] matrix = {{1, 2, 3}, {4, 5, 6}, {7, 8, 9}};
        int target = 5;
        boolean found2d = false;
        for (int[] row : matrix) {
            for (int val : row) {
                if (val == target) {
                    found2d = true;
                    break;  // only exits inner loop!
                }
            }
            if (found2d) break;  // also need to exit outer loop
        }
        System.out.println("Found " + target + ": " + found2d);
    }
}
```

**What this does:** `break` exits only the innermost loop/switch. To break out of nested loops, you need either a flag variable (as shown) or a labeled break.

### Example 2 — continue

```java
public class ContinueDemo {
    public static void main(String[] args) {
        // Print only odd numbers
        for (int i = 0; i <= 10; i++) {
            if (i % 2 == 0) continue;  // skip even numbers
            System.out.print(i + " ");
        }
        System.out.println(); // 1 3 5 7 9

        // Skip specific values
        int[] data = {1, -1, 3, -5, 7, -2, 9};
        int sum = 0;
        for (int n : data) {
            if (n < 0) continue;  // skip negatives
            sum += n;
        }
        System.out.println("Sum of positives: " + sum); // 20
    }
}
```

**What this does:** `continue` jumps to the next iteration — for `for` loops it executes the update first; for `while` it goes to the condition check. Useful to skip special cases without deep nesting.

### Example 3 — Labeled break and continue

```java
public class LabeledBreak {
    public static void main(String[] args) {
        // Labeled break: exit OUTER loop from INNER loop
        outer:  // label for the outer loop
        for (int i = 0; i < 5; i++) {
            for (int j = 0; j < 5; j++) {
                if (i + j == 6) {
                    System.out.println("Breaking at i=" + i + " j=" + j);
                    break outer;  // exits outer loop entirely!
                }
            }
        }
        System.out.println("After labeled break");

        // Labeled continue: skip to next iteration of OUTER loop
        System.out.println("--- Labeled continue ---");
        loop:
        for (int i = 0; i < 3; i++) {
            for (int j = 0; j < 3; j++) {
                if (j == 1) continue loop;  // skip rest of inner, next i
                System.out.println("i=" + i + " j=" + j);
            }
        }
        // Only prints j=0 for each i
    }
}
```

**What this does:** Labels let you target a specific outer loop. `break outer` exits the labeled loop entirely. `continue loop` skips to the next iteration of the labeled loop, skipping any remaining inner loop iterations.

### Dry Run — Labeled break Trace

```java
outer:
for (int i = 0; i < 3; i++) {
    for (int j = 0; j < 3; j++) {
        if (i == 1 && j == 1) break outer;
        System.out.println(i + "," + j);
    }
}
```

| i | j | Condition `i==1 && j==1` | Action         | Output |
|---|---|--------------------------|----------------|--------|
| 0 | 0 | false                    | print          | "0,0"  |
| 0 | 1 | false                    | print          | "0,1"  |
| 0 | 2 | false                    | print          | "0,2"  |
| 1 | 0 | false                    | print          | "1,0"  |
| 1 | 1 | **true**                 | `break outer`  | —      |
| — | — | outer loop exited        | done           | —      |

Pairs `1,1`, `1,2`, `2,0`, `2,1`, `2,2` are never printed.

> ⚠️ **Pitfall:** Labeled statements are often a sign that your logic should be extracted to a method. A `return` from a method is usually cleaner than a labeled break.

---

## 8. Quick Reference

```
if/else if/else    → check boolean conditions in order, first match wins
classic switch     → match variable against constants; WATCH for fall-through (missing break)
switch expression  → [Java 14+] arrow syntax, no fall-through, can return value, use yield for blocks
for loop           → use when iterations are known: for(init; condition; update)
for-each           → use for arrays/collections when no index needed; can't modify or remove
while              → use when iterations unknown, condition checked BEFORE body
do-while           → use when body must execute at least once, condition checked AFTER body
break              → exits innermost loop/switch; label targets outer loop
continue           → skips current iteration; label targets outer loop
```

```
Common pitfalls:
- Missing break in classic switch → fall-through
- For-each element modification → only modifies local copy
- Modifying collection during for-each → ConcurrentModificationException
- Dangling else → else pairs with nearest if
- while(condition) with no update → infinite loop
```
