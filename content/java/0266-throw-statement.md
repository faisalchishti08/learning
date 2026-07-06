---
card: java
gi: 266
slug: throw-statement
title: throw statement
---

## 1. What it is

The `throw` statement is how you actually raise an exception yourself: `throw someThrowableInstance;` immediately stops normal execution at that point and begins propagating the given exception object up the call stack, looking for a matching `catch` clause. The operand must be an actual instance of `Throwable` (or one of its subclasses) — you cannot `throw` an arbitrary value like a `String` or an `int`.

```java
public class ThrowStatementDemo {
    static void validateAge(int age) {
        if (age < 0) {
            throw new IllegalArgumentException("age cannot be negative: " + age); // raises the exception here
        }
        System.out.println("Age " + age + " is valid");
    }

    public static void main(String[] args) {
        try {
            validateAge(-5);
        } catch (IllegalArgumentException e) {
            System.out.println("Rejected: " + e.getMessage());
        }
    }
}
```

`throw new IllegalArgumentException(...)` both creates a new exception object (with `new`, exactly like creating any other object) and immediately raises it, stopping `validateAge`'s execution at that exact line — the rest of the method (the `System.out.println` after the `if`) never runs, and control transfers straight to the nearest matching `catch` clause in `main`.

## 2. Why & when

The `throw` statement is how your own code signals that it cannot proceed normally, handing off the decision of how to respond to whatever caller is positioned to catch the exception.

- **Signaling a violated precondition or invalid state** — the standard use is validating input or internal state and raising an appropriate exception the moment something is wrong, rather than continuing to execute with data you know is invalid, which could produce subtly wrong results far from the actual root cause.
- **Interrupting normal control flow deliberately** — `throw`, like `return`, immediately exits the current block of code; unlike `return`, it doesn't just exit the current method — it continues propagating up through every enclosing method call until something catches it, or the program terminates if nothing does.
- **Rethrowing a caught exception** — `throw` is also used inside a `catch` block to deliberately let an exception continue propagating further (possibly after logging it, or wrapped in a different exception type, as an earlier topic on checked exceptions demonstrated), rather than fully handling it right there.

Use `throw` the moment your code detects a condition it cannot or should not proceed past — validate as early as possible (a well-known principle sometimes called "fail fast") so that errors are caught close to their actual cause, rather than allowing invalid data or state to propagate silently deeper into the program before eventually causing a much more confusing failure somewhere else.

## 3. Core concept

```java
public class ThrowCore {
    static double calculateAverage(int[] values) {
        if (values.length == 0) {
            throw new IllegalArgumentException("cannot compute average of an empty array");
        }
        int sum = 0;
        for (int v : values) sum += v;
        return (double) sum / values.length;
    }
}
```

`throw` here fires *before* any division happens, immediately signaling the actual problem (an empty array, which would otherwise cause a division by zero producing a confusing `NaN` result rather than a clear error) — this is "failing fast": catching the invalid condition at the earliest possible point, with a message that directly explains what went wrong, rather than letting a symptom of the real problem surface somewhere else entirely.

## 4. Diagram

<svg viewBox="0 0 600 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A throw statement immediately stops normal execution at that exact point and begins propagating the exception object up through every enclosing method call looking for a matching catch clause">
  <rect x="8" y="8" width="584" height="154" rx="8" fill="#0d1117"/>

  <rect x="40" y="20" width="180" height="30" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="130" y="40" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">calculateAverage()</text>

  <rect x="40" y="60" width="180" height="30" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="2"/>
  <text x="130" y="80" fill="#f85149" font-size="9" text-anchor="middle" font-family="monospace">throw new IllegalArg...()</text>

  <line x1="220" y1="75" x2="330" y2="75" stroke="#f85149" stroke-width="1.5"/>
  <text x="275" y="65" fill="#f85149" font-size="8" text-anchor="middle" font-family="sans-serif">propagates up</text>

  <rect x="330" y="60" width="220" height="30" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="440" y="80" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">nearest matching catch</text>

  <text x="300" y="130" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Everything after the throw statement in the current method never executes.</text>
</svg>

`throw` stops execution immediately at that point and propagates the exception object upward until something catches it.

## 5. Runnable example

Scenario: a bank withdrawal routine using `throw` to enforce business rules, evolved from a single validation into several combined guard clauses, then hardened with a case demonstrating rethrowing after partial handling.

### Level 1 — Basic

```java
public class ThrowBasic {
    static void withdraw(double balance, double amount) {
        if (amount > balance) {
            throw new IllegalStateException("insufficient funds: balance=" + balance + ", requested=" + amount);
        }
        System.out.println("Withdrew $" + amount + ", remaining balance: $" + (balance - amount));
    }

    public static void main(String[] args) {
        try {
            withdraw(100.0, 150.0);
        } catch (IllegalStateException e) {
            System.out.println("Withdrawal failed: " + e.getMessage());
        }
    }
}
```

**How to run:** `java ThrowBasic.java`

`throw new IllegalStateException(...)` fires the moment the requested amount exceeds the balance, stopping `withdraw` before it ever prints a (nonsensical) negative remaining balance.

### Level 2 — Intermediate

Same withdrawal logic, now with multiple guard clauses using `throw`, each catching a distinct invalid condition before any actual withdrawal logic runs.

```java
public class ThrowIntermediate {
    static void withdraw(double balance, double amount) {
        if (amount <= 0) {
            throw new IllegalArgumentException("withdrawal amount must be positive, got: " + amount);
        }
        if (amount > balance) {
            throw new IllegalStateException("insufficient funds: balance=" + balance + ", requested=" + amount);
        }
        System.out.println("Withdrew $" + amount + ", remaining balance: $" + (balance - amount));
    }

    public static void main(String[] args) {
        double[][] attempts = { {100.0, -10.0}, {100.0, 150.0}, {100.0, 50.0} };
        for (double[] attempt : attempts) {
            try {
                withdraw(attempt[0], attempt[1]);
            } catch (IllegalArgumentException e) {
                System.out.println("Invalid amount: " + e.getMessage());
            } catch (IllegalStateException e) {
                System.out.println("Cannot complete: " + e.getMessage());
            }
        }
    }
}
```

**How to run:** `java ThrowIntermediate.java`

Each guard clause throws a distinct exception type for a distinct violated rule — a negative amount versus an amount exceeding the balance — and each is caught with its own tailored message, demonstrating `throw` used for genuinely different precondition failures within the same method.

### Level 3 — Advanced

Same withdrawal system, now demonstrating `throw` used inside a `catch` block to rethrow after logging — a common pattern where a method wants to observe or record a failure without fully absorbing responsibility for handling it, letting the exception continue propagating to its actual caller.

```java
public class ThrowAdvanced {
    static void withdraw(double balance, double amount) {
        if (amount <= 0) {
            throw new IllegalArgumentException("withdrawal amount must be positive, got: " + amount);
        }
        if (amount > balance) {
            throw new IllegalStateException("insufficient funds: balance=" + balance + ", requested=" + amount);
        }
        System.out.println("Withdrew $" + amount + ", remaining balance: $" + (balance - amount));
    }

    static void auditedWithdraw(double balance, double amount) {
        try {
            withdraw(balance, amount);
        } catch (RuntimeException e) {
            System.out.println("[AUDIT LOG] Withdrawal attempt failed: " + e.getMessage());
            throw e; // rethrow: log it here, but let the ACTUAL caller decide how to respond
        }
    }

    public static void main(String[] args) {
        try {
            auditedWithdraw(100.0, 150.0);
        } catch (IllegalStateException e) {
            System.out.println("Final handler: informing the user — " + e.getMessage());
        }
    }
}
```

**How to run:** `java ThrowAdvanced.java`

`auditedWithdraw` catches the exception just long enough to log it (`"[AUDIT LOG] ..."`), then executes `throw e;` to rethrow the *exact same* exception object, letting it continue propagating to `main` — this is a deliberate use of `throw` for observing a failure at an intermediate layer without fully handling it there, preserving the original exception (including its stack trace) for whatever layer actually decides how to respond.

## 6. Walkthrough

Trace `main` in `ThrowAdvanced` step by step.

**`auditedWithdraw(100.0, 150.0)`.** Inside its `try` block, `withdraw(100.0, 150.0)` is called. Inside `withdraw`: `amount <= 0` is `false` (`150.0` is positive), so the first guard passes. `amount > balance` is `true` (`150.0 > 100.0`), so `throw new IllegalStateException("insufficient funds: balance=100.0, requested=150.0")` fires immediately — nothing after this line in `withdraw` executes.

**The exception propagates back into `auditedWithdraw`'s `catch (RuntimeException e)` clause** (since `IllegalStateException` is a `RuntimeException` subtype). It prints `"[AUDIT LOG] Withdrawal attempt failed: insufficient funds: balance=100.0, requested=150.0"`. Then `throw e;` executes: this re-raises the *same* exception object (`e`) — not a new one — so its original stack trace and all its data remain completely intact.

**This rethrown exception propagates out of `auditedWithdraw`** and is caught in `main`'s `catch (IllegalStateException e)` clause. It prints `"Final handler: informing the user — insufficient funds: balance=100.0, requested=150.0"`.

```
auditedWithdraw(100.0, 150.0):
  try: withdraw(100.0, 150.0)
    amount<=0? false
    amount>balance? true (150.0 > 100.0) -> throw IllegalStateException("insufficient funds: ...")

  catch (RuntimeException e) in auditedWithdraw:
    prints "[AUDIT LOG] Withdrawal attempt failed: insufficient funds: ..."
    throw e; -> rethrows the SAME exception object, propagates further

main catches IllegalStateException:
  prints "Final handler: informing the user — insufficient funds: ..."
```

**Final output.**
```
[AUDIT LOG] Withdrawal attempt failed: insufficient funds: balance=100.0, requested=150.0
Final handler: informing the user — insufficient funds: balance=100.0, requested=150.0
```
Both messages reference the identical underlying failure, since `throw e;` rethrew the exact same exception object rather than constructing a new one — this preserves the complete original stack trace, which would matter greatly for debugging in a real, more complex call chain.

## 7. Gotchas & takeaways

> **`throw` immediately halts execution at that exact statement — nothing after it in the same block runs, ever, for that invocation.** Unlike an `if`/`else` that might skip only part of a method, `throw` unwinds out of the current method entirely (and further, up the call stack) until a matching `catch` is found, making it a much more drastic control-flow jump than most other statements.

> **`throw e;` (rethrowing the exact same caught exception object) preserves the original stack trace, which is different from `throw new SomeException(e.getMessage());` (constructing a brand-new exception)** — the latter would discard the original stack trace entirely, replacing it with a new one pointing to the rethrow location, losing valuable information about where the failure actually originated. When you need to add context while rethrowing, prefer wrapping the original exception as a "cause" (as an earlier checked-exceptions topic demonstrated) rather than discarding it.

- `throw someThrowable;` immediately stops normal execution and begins propagating the given exception object up the call stack toward a matching `catch` clause.
- Use `throw` to fail fast: raise an exception the moment your code detects a condition it cannot proceed past, as close to the root cause as possible.
- `throw` can also rethrow an already-caught exception (`throw e;`) inside a `catch` block, useful for logging or auditing a failure without fully absorbing responsibility for handling it.
- Rethrowing the original exception object (rather than constructing a new one) preserves its original stack trace, which matters significantly for debugging.
