---
card: java
gi: 255
slug: capturing-local-variables-final-effectively-final
title: Capturing local variables (final/effectively-final)
---

## 1. What it is

A local or anonymous class can read a local variable or parameter from its enclosing method, but only if that variable is `final` or "effectively final" — meaning it is assigned exactly once and never reassigned anywhere after that, even though the `final` keyword itself is optional. Attempting to capture a variable that *is* reassigned somewhere later in the method is a compile error.

```java
public class CaptureDemo {
    interface Printer { void print(); }

    static Printer makePrinter(String message) { // message is a parameter, never reassigned -> effectively final
        return new Printer() {
            @Override
            public void print() {
                System.out.println(message); // capturing message: legal, since it's effectively final
            }
        };
    }

    public static void main(String[] args) {
        makePrinter("Hello from capture!").print();
    }
}
```

`message` is never reassigned anywhere inside `makePrinter` after being received as a parameter, so it is effectively final, and the anonymous `Printer` implementation is allowed to capture and read it — if `message` were reassigned even once later in the method (say, `message = message + "!"`), the capture inside the anonymous class would fail to compile.

## 2. Why & when

This rule exists because of a fundamental lifetime mismatch: a local variable normally disappears the moment its enclosing method returns, but a local or anonymous class instance capturing it can easily outlive that method call.

- **Solving the lifetime mismatch** — if `makePrinter` returns and its stack frame is destroyed, `message` as a local variable no longer exists in the usual sense; Java solves this by having the anonymous class capture a private *copy* of the variable's value at the time it was created, rather than a live reference to the original local variable slot.
- **Requiring effective finality guarantees the copy stays accurate** — if the variable could be reassigned after being captured, the captured copy and the "real" variable could drift apart, creating confusing inconsistencies about which value is "the" value; requiring the variable never change after capture avoids this entirely.
- **This is exactly why loop variables commonly need special handling** — a traditional `for (int i = 0; ...; i++)` loop variable is reassigned every iteration, so it can never be captured directly; this is why the previous local-class topic's example declared a *new* `final int lineNumber` inside the loop body specifically to create a fresh, effectively final variable each iteration.

Whenever a local or anonymous class needs to use a value from its enclosing method, ensure that value is assigned exactly once — for values that naturally change (like a loop counter), copy the current value into a new, unreassigned local variable at the point where the local or anonymous class captures it, exactly as the previous topic's `lineNumber` pattern demonstrated.

## 3. Core concept

```java
import java.util.function.Supplier;

public class CaptureCore {
    static Supplier<Integer> makeCounter(int start) {
        // int current = start; // if THIS were reassigned later, capturing it below would fail to compile
        return () -> start + 1; // captures 'start' — legal, since start is never reassigned in this method
    }

    public static void main(String[] args) {
        System.out.println(makeCounter(5).get()); // 6
    }
}
```

`start` is a parameter never reassigned anywhere in `makeCounter`, so the lambda (which, like an anonymous class, follows the same capture rules) can legally read it; the lambda effectively holds on to the value `5` even after `makeCounter` itself has returned and its stack frame is long gone.

## 4. Diagram

<svg viewBox="0 0 600 180" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A method local variable is copied into the captured state of a local or anonymous class at creation time, the method can then return and its stack frame vanish while the captured copy lives on inside the object">
  <rect x="8" y="8" width="584" height="164" rx="8" fill="#0d1117"/>

  <rect x="40" y="20" width="220" height="50" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
  <text x="150" y="40" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">makePrinter(String message)</text>
  <text x="150" y="56" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">stack frame — will vanish on return</text>

  <line x1="260" y1="45" x2="340" y2="45" stroke="#8b949e" stroke-width="1.5"/>
  <text x="300" y="35" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">copy at creation</text>

  <rect x="340" y="20" width="220" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="450" y="40" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">Printer instance</text>
  <text x="450" y="56" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">holds its own copy of message</text>

  <text x="300" y="110" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">makePrinter's stack frame is gone after it returns,</text>
  <text x="300" y="128" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">but the Printer instance still has its own copy of "message" —</text>
  <text x="300" y="146" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">which is only safe because message was never reassigned.</text>
</svg>

Capturing copies the value at creation time; requiring effective finality guarantees that copy is never stale.

## 5. Runnable example

Scenario: a batch of deferred greeting tasks built inside a loop, evolved from a broken naive attempt (shown as a compile error) into a correct effectively-final pattern, then hardened with a mutable workaround using a single-element array for cases genuinely needing shared, mutable captured state.

### Level 1 — Basic

```java
import java.util.ArrayList;
import java.util.List;

public class CaptureBasic {
    interface Task { void run(); }

    public static void main(String[] args) {
        List<Task> tasks = new ArrayList<>();

        for (int i = 0; i < 3; i++) {
            final int taskNumber = i; // a NEW effectively-final variable each iteration
            tasks.add(() -> System.out.println("Running task " + taskNumber));
        }

        for (Task t : tasks) t.run();
    }
}
```

**How to run:** `java CaptureBasic.java`

`taskNumber` is declared fresh inside the loop body on every iteration and never reassigned afterward, so each lambda correctly captures *that iteration's* value — printing `0`, `1`, and `2` respectively, rather than all three lambdas somehow sharing one final value of `3` (which would be the outcome if `i` itself, the reassigned loop variable, could be captured directly — it cannot, precisely because of this rule).

### Level 2 — Intermediate

Same task list, now demonstrating the compile error that results from attempting to capture a variable that *is* reassigned — shown as a comment, since it would prevent the file from compiling — followed by the corrected version.

```java
import java.util.ArrayList;
import java.util.List;

public class CaptureIntermediate {
    interface Task { void run(); }

    public static void main(String[] args) {
        List<Task> tasks = new ArrayList<>();

        int runningTotal = 0; // NOT effectively final -- it gets reassigned below
        for (int i = 0; i < 3; i++) {
            runningTotal += i; // this reassignment is exactly why runningTotal cannot be captured directly

            // tasks.add(() -> System.out.println("Total so far: " + runningTotal));
            // COMPILE ERROR if uncommented: "local variables referenced from a lambda expression
            // must be final or effectively final"

            final int snapshot = runningTotal; // FIX: copy the CURRENT value into a fresh, unreassigned variable
            tasks.add(() -> System.out.println("Total so far: " + snapshot));
        }

        for (Task t : tasks) t.run();
    }
}
```

**How to run:** `java CaptureIntermediate.java`

`runningTotal` is reassigned every iteration (`runningTotal += i`), so it can never be captured directly by a lambda or anonymous class; the fix is to copy its *current* value into `snapshot`, a brand-new variable created fresh each iteration and never reassigned afterward — `snapshot` is effectively final within each iteration's own scope, even though the value it was copied from keeps changing across iterations.

### Level 3 — Advanced

Same idea, now demonstrating the standard workaround for genuinely needing *shared, mutable* state accessible from inside a lambda or anonymous class: wrapping the mutable value in a single-element array (or an `AtomicInteger`/similar), since the array *reference* itself is what gets captured, and that reference never changes even though the array's contents can.

```java
import java.util.ArrayList;
import java.util.List;

public class CaptureAdvanced {
    interface Task { void run(); }

    public static void main(String[] args) {
        List<Task> tasks = new ArrayList<>();

        int[] sharedCounter = {0}; // the ARRAY REFERENCE is effectively final; its CONTENTS can still change

        for (int i = 0; i < 3; i++) {
            tasks.add(() -> {
                sharedCounter[0]++; // mutating the array's element, not reassigning the reference itself
                System.out.println("Shared counter is now: " + sharedCounter[0]);
            });
        }

        for (Task t : tasks) t.run(); // each run() increments and prints the SAME shared counter
    }
}
```

**How to run:** `java CaptureAdvanced.java`

`sharedCounter` (the array reference) is assigned exactly once and never reassigned, so it is effectively final and legally captured by every lambda created in the loop — but because it is an *array*, its single element, `sharedCounter[0]`, can still be mutated freely through that reference, giving all three lambdas access to one genuinely shared, mutable counter, which is the standard idiom for this need in Java.

## 6. Walkthrough

Trace `main` in `CaptureAdvanced` from the loop through the final task executions.

**Loop iteration `i=0`.** A lambda is created and added to `tasks`. It captures `sharedCounter` (the array reference, unchanged throughout the whole program) — no snapshot copying is needed here, since it's the reference, not a primitive value, being captured.

**Loop iterations `i=1` and `i=2`.** Two more lambdas are created and added, each also capturing the exact same `sharedCounter` reference (there is only ever one array object throughout).

**`tasks.get(0).run()` (first task).** Executes `sharedCounter[0]++`: reads the current value (`0`), increments the array's element to `1`. Prints `"Shared counter is now: 1"`.

**`tasks.get(1).run()` (second task).** Executes `sharedCounter[0]++` again: reads the current value (`1`, left over from the previous task, since all three lambdas share the same array), increments to `2`. Prints `"Shared counter is now: 2"`.

**`tasks.get(2).run()` (third task).** Executes `sharedCounter[0]++`: reads `2`, increments to `3`. Prints `"Shared counter is now: 3"`.

```
sharedCounter = [0]  (one array, one reference, captured by all three lambdas)

task 0 runs: sharedCounter[0]: 0 -> 1, prints "Shared counter is now: 1"
task 1 runs: sharedCounter[0]: 1 -> 2, prints "Shared counter is now: 2"
task 2 runs: sharedCounter[0]: 2 -> 3, prints "Shared counter is now: 3"
```

**Final output.**
```
Shared counter is now: 1
Shared counter is now: 2
Shared counter is now: 3
```
This confirms all three lambdas are genuinely sharing and mutating the same underlying array, unlike the effectively-final primitive captures in the earlier examples, where each lambda held its own independent, frozen snapshot value.

## 7. Gotchas & takeaways

> **The compile error "local variables referenced from a lambda expression must be final or effectively final" (or the equivalent for anonymous/local classes) means exactly one thing: the variable in question is reassigned somewhere in the enclosing method after the point of capture.** The fix is almost always either (a) stop reassigning it, (b) copy its current value into a fresh, never-reassigned variable at the point of capture, or (c) if genuinely shared mutable state is required, wrap it in a single-element array or a dedicated mutable holder like `AtomicInteger`.

> **Capturing a primitive or a `String` copies the *value* at creation time; capturing a reference to a mutable object (like an array, `List`, or custom class) copies the *reference*, but the object it points to can still be mutated through that reference.** This is why `sharedCounter[0]++` works even though `sharedCounter` itself is "effectively final" — the array reference never changes, only the data inside the array does, and that distinction is exactly what makes controlled mutable capture possible in Java.

- Local and anonymous classes (and lambdas) can only capture local variables and parameters that are `final` or effectively final — assigned exactly once, never reassigned afterward.
- This restriction exists because the captured variable's lifetime can outlive the enclosing method's stack frame; Java handles this by capturing a fixed copy, which is only safe if that value never changes.
- Loop variables that are reassigned each iteration cannot be captured directly; copy the current value into a fresh, per-iteration variable instead.
- To share genuinely mutable state across multiple captures, capture a reference to a mutable container (a single-element array, or a class like `AtomicInteger`) rather than a primitive value directly.
