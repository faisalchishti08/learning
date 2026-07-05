---
card: java
gi: 129
slug: if-else-statement
title: if-else statement
---

## 1. What it is

`if`/`else` extends the plain `if` statement with an alternative branch: if the condition is `true`, the `if` block executes; if `false`, the `else` block executes instead. Exactly one of the two blocks always runs — never both, never neither — which makes `if`/`else` the standard tool for genuinely binary decisions, as opposed to a bare `if` (which only handles "do this, or do nothing").

```java
int score = 55;
if (score >= 60) {
    System.out.println("Pass");
} else {
    System.out.println("Fail");
}
// exactly one of "Pass"/"Fail" prints, always
```

The `else` block is entirely optional syntactically (a plain `if` is just `if`/`else` with an empty, implicit `else`), but once present, it guarantees full coverage of both the `true` and `false` cases for that one condition — useful for reasoning about a piece of logic exhaustively, since there is no "fallthrough gap" the way there might be with a chain of independent `if` statements that don't cover every case.

## 2. Why & when

`if`/`else` is used whenever exactly one of two alternative actions must happen, and forgetting to handle the "false" case would be a bug:

- Validating and branching: `if (isValid) { process(); } else { reportError(); }`.
- Toggling between two states or behaviors: `if (isDarkMode) { applyDarkTheme(); } else { applyLightTheme(); }`.
- Handling a special case versus the general case: `if (list.isEmpty()) { return defaultValue; } else { return list.get(0); }`.

Prefer `if`/`else` over two independent `if` statements whenever the two branches are truly mutually exclusive alternatives of the *same* decision — writing `if (cond) {...}` followed by a separate `if (!cond) {...}` is functionally similar but re-evaluates (or manually re-negates) the condition, and is more fragile to maintain if the condition later changes, since the negation has to be kept in sync by hand.

## 3. Core concept

```java
public class IfElseDemo {
    public static void main(String[] args) {
        int score = 55;

        // Basic if/else: exactly one branch runs
        if (score >= 60) {
            System.out.println("Pass");
        } else {
            System.out.println("Fail");
        }

        // Preferred over two independent, manually-negated ifs:
        boolean isEven = (score % 2 == 0);
        if (isEven) {
            System.out.println("Even");
        } else {
            System.out.println("Odd");
        }
        // NOT this fragile alternative:
        // if (isEven) { System.out.println("Even"); }
        // if (!isEven) { System.out.println("Odd"); }   <- must stay manually in sync with the first condition

        // if/else as the "default value" pattern
        int[] data = {};
        int firstOrDefault;
        if (data.length > 0) {
            firstOrDefault = data[0];
        } else {
            firstOrDefault = -1;
        }
        System.out.println("firstOrDefault: " + firstOrDefault);

        // Both branches can themselves contain multiple statements
        boolean maintenanceMode = false;
        if (maintenanceMode) {
            System.out.println("Site is down for maintenance.");
            System.out.println("Please check back later.");
        } else {
            System.out.println("Welcome!");
            System.out.println("Loading dashboard...");
        }
    }
}
```

## 4. Diagram

<svg viewBox="0 0 700 155" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="if-else control flow diagram: execution reaches the condition check, if true it enters the if block, if false it enters the else block instead, and exactly one of the two blocks always runs before execution continues at the same point after the if-else statement.">
  <rect x="8" y="8" width="684" height="139" rx="8" fill="#0d1117"/>
  <text x="350" y="24" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">if (condition) { A } else { B } — exactly one of A, B always runs</text>

  <rect x="290" y="34" width="120" height="30" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="350" y="54" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">condition?</text>

  <path d="M 320 64 L 200 90" stroke="#6db33f" stroke-width="1.5"/>
  <text x="240" y="80" fill="#6db33f" font-size="8">true</text>
  <rect x="100" y="90" width="200" height="34" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="200" y="112" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">A: if-block runs</text>

  <path d="M 380 64 L 500 90" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="460" y="80" fill="#79c0ff" font-size="8">false</text>
  <rect x="400" y="90" width="200" height="34" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="500" y="112" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">B: else-block runs</text>

  <text x="350" y="140" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Both paths converge and continue after the statement — coverage is exhaustive, no gap.</text>
</svg>

Unlike a bare `if`, `if`/`else` covers both possible outcomes of the condition — there is no case where neither block runs.

## 5. Runnable example

Scenario: a login-attempt handler that either grants access or records a failed attempt — starting simply, then extended to lock the account after repeated failures, then hardened against a subtle bug where a later refactor accidentally broke the exhaustive either/or guarantee.

### Level 1 — Basic

```java
public class LoginBasic {
    public static void main(String[] args) {
        String correctPassword = "hunter2";
        String attempt = "wrongpass";

        if (attempt.equals(correctPassword)) {
            System.out.println("Access granted.");
        } else {
            System.out.println("Access denied.");
        }
    }
}
```

**How to run:** `java LoginBasic.java`

`attempt.equals(correctPassword)` evaluates to `false` for this mismatched attempt, so the `else` branch runs, printing `"Access denied."` — exactly one of the two messages is guaranteed to print for any pair of strings, since `.equals()` always returns a definite `true` or `false`.

### Level 2 — Intermediate

Same login handler, now tracking failed attempts and locking the account after three failures, using nested `if`/`else` to handle the combination of "was this attempt correct" and "how many failures have accumulated."

```java
public class LoginIntermediate {

    static int failedAttempts = 0;
    static final int MAX_ATTEMPTS = 3;

    static void attemptLogin(String correctPassword, String attempt) {
        if (attempt.equals(correctPassword)) {
            System.out.println("Access granted.");
            failedAttempts = 0;   // reset on success
        } else {
            failedAttempts++;
            if (failedAttempts >= MAX_ATTEMPTS) {
                System.out.println("Account locked after " + failedAttempts + " failed attempts.");
            } else {
                System.out.println("Access denied. Attempt " + failedAttempts + " of " + MAX_ATTEMPTS + ".");
            }
        }
    }

    public static void main(String[] args) {
        String correctPassword = "hunter2";
        attemptLogin(correctPassword, "wrong1");
        attemptLogin(correctPassword, "wrong2");
        attemptLogin(correctPassword, "wrong3");
        attemptLogin(correctPassword, "hunter2");  // too late — already locked, but this demo doesn't check that yet
    }
}
```

**How to run:** `java LoginIntermediate.java`

The outer `if`/`else` handles "was the attempt correct or not" — exactly one of those two branches always runs. Within the `else` (incorrect attempt) branch, a second, nested `if`/`else` handles "has the failure count now reached the lockout threshold or not" — again, exactly one of those two sub-branches always runs whenever the outer `else` is reached. This layered structure correctly reports "Account locked" only once the third failure occurs, and a normal "Access denied, attempt N of 3" message for the first two failures.

### Level 3 — Advanced

Same login handler, now demonstrating a real bug that can arise when a later "helpful" refactor breaks the exhaustive either/or guarantee: someone adds an early `return` intending to short-circuit a locked account, but does so *outside* the original `if`/`else`, silently allowing the message logic beneath it to run unintentionally for a case that should have been fully handled by the early return.

```java
public class LoginAdvanced {

    static int failedAttempts = 0;
    static boolean locked = false;
    static final int MAX_ATTEMPTS = 3;

    static void attemptLogin(String correctPassword, String attempt) {
        if (locked) {
            System.out.println("Account is locked. Contact support.");
            return;   // correctly exits BEFORE any further logic
        }

        if (attempt.equals(correctPassword)) {
            System.out.println("Access granted.");
            failedAttempts = 0;
        } else {
            failedAttempts++;
            if (failedAttempts >= MAX_ATTEMPTS) {
                locked = true;
                System.out.println("Account locked after " + failedAttempts + " failed attempts.");
            } else {
                System.out.println("Access denied. Attempt " + failedAttempts + " of " + MAX_ATTEMPTS + ".");
            }
        }
    }

    public static void main(String[] args) {
        String correctPassword = "hunter2";
        attemptLogin(correctPassword, "wrong1");
        attemptLogin(correctPassword, "wrong2");
        attemptLogin(correctPassword, "wrong3");   // this triggers the lock
        attemptLogin(correctPassword, "hunter2");    // correct password, but now correctly blocked by the lock check
    }
}
```

**How to run:** `java LoginAdvanced.java`

The `if (locked) { ...; return; }` guard clause at the very top is checked *before* the main `if`/`else` even runs, and its `return` statement ensures that once an account is locked, none of the subsequent login logic executes at all for that call — this correctly preserves the "exactly one exhaustive outcome" property by making the lock check itself an earlier, separate, and equally exhaustive `if` (locked, so return immediately; or not locked, so fall through to the rest of the method). The final `attemptLogin` call demonstrates this directly: even though `"hunter2"` is the correct password, the account is already locked from the third failed attempt, so the `if (locked)` guard catches it first and the correct-password branch of the inner `if`/`else` never even runs — a subtle but important interaction between an early guard clause and a subsequent `if`/`else`, and a common source of bugs if the guard clause is accidentally placed *after* rather than *before* the main logic.

## 6. Walkthrough

Trace the fourth `attemptLogin(correctPassword, "hunter2")` call, after the account has already been locked by the third failed attempt:

**Guard clause check.** `if (locked)` evaluates `locked`, which was set to `true` during the third call's `else` branch (specifically, inside its nested `if (failedAttempts >= MAX_ATTEMPTS)` branch). Since `locked` is `true`, this condition is `true`.

**Guard clause executes and returns.** The method prints `"Account is locked. Contact support."` and then executes `return;`, which immediately exits `attemptLogin` — no further code in the method body runs for this call.

**The main `if`/`else` never runs.** Even though `attempt.equals(correctPassword)` would have evaluated to `true` for this call (the password *is* correct), that comparison is never even reached, because the `return` inside the guard clause already exited the method before execution could get there.

```
attemptLogin(correctPassword, "hunter2")   [4th call, after lock]

if (locked)?             true (set during 3rd call)
    print "Account is locked..."
    return                                  <- exits HERE

if (attempt.equals(...))  <- NEVER REACHED, even though it would have been true
    ...
else
    ...
```

**Why this matters as a design lesson.** If the guard clause had instead been written *without* the `return` (or placed after the main `if`/`else` instead of before it), the correct-password branch could have executed anyway, incorrectly granting access to a locked account — this demonstrates that `if`/`else`'s "exactly one branch always runs" guarantee only applies *within* a single `if`/`else` construct; when multiple independent `if` statements (a guard clause plus a main `if`/`else`) are chained together in a method, the overall correctness depends on ensuring earlier guards genuinely prevent later code from running when they should, typically via an explicit `return` (or `break`/`continue` in a loop context).

## 7. Gotchas & takeaways

> **`if`/`else` guarantees exactly one of its two branches runs for that specific condition — but chaining multiple independent `if` statements (like a guard clause followed by a separate `if`/`else`) does not automatically preserve overall exhaustiveness unless earlier guards explicitly exit (via `return`, `break`, `continue`, or a thrown exception) to prevent later code from running.**

> **Prefer `if`/`else` over two separately negated `if` statements checking the same condition and its logical opposite.** The `if`/`else` form only requires the condition to be written once, so it can never fall out of sync with itself — writing `if (cond)` and `if (!cond)` as two separate statements requires manually keeping the negation correct if `cond`'s expression is ever edited.

- `if`/`else` guarantees exactly one of its two blocks executes: never both, never neither.
- Use `if`/`else` (not two independent, manually negated `if` statements) whenever two branches represent genuinely mutually exclusive alternatives of the same decision.
- Nesting `if`/`else` inside another branch is a common way to handle combinations of conditions, but each level of nesting should still preserve its own local exhaustiveness.
- When chaining a guard clause before a main `if`/`else`, make sure the guard actually exits (via `return` or similar) rather than merely printing a message and falling through — otherwise the code after it may run unintentionally.
