---
card: java
gi: 760
slug: unnamed-variables-patterns-standardized
title: Unnamed variables & patterns — standardized
---

## 1. What it is

**Java 22** (JEP 456) makes [unnamed variables and patterns](0751-unnamed-patterns-variables-preview.md) — the `_` stand-in for a value the language requires syntactically but the code never reads — a **permanent, standard feature**, no `--enable-preview` flag needed, after its single preview round in Java 21. `_` in a `catch` clause, a lambda parameter, a `for` loop variable, or a record pattern component is now ordinary, production-ready Java syntax.

## 2. Why & when

A single preview round was enough to validate this feature because, unlike bigger structural changes, `_` is a narrowly scoped, low-risk piece of syntax: it doesn't change how any existing code behaves (code that already uses `_` as an actual identifier — legal, if discouraged, before this feature — needed a one-time compatibility check, which the JDK team resolved by making single-underscore `_` a compile error as a *declared* identifier from Java 21 onward, reserving it exclusively for this unnamed-variable role). With that resolved, and community feedback from Java 21's preview confirming the syntax and its scope rules held up as designed, moving straight to standard in Java 22 reflects that this was a well-contained addition rather than one still searching for its final shape. Since it's standardized, any linter, style guide, or team convention that wants to enforce "mark genuinely unused bindings with `_`" can now do so without a preview-feature caveat attached.

## 3. Core concept

```java
record Point(int x, int y) {}
record Rectangle(Point topLeft, Point bottomRight) {}

static boolean isAtOrigin(Object shape) {
    // No --enable-preview needed — this is standard Java 22 syntax.
    if (shape instanceof Rectangle(Point(int x, int y), _)) {
        return x == 0 && y == 0;
    }
    return false;
}
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Unnamed variables move from a single Java 21 preview round directly to standard status in Java 22">
  <rect x="40" y="20" width="220" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="150" y="50" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Java 21: preview (1 round)</text>

  <line x1="260" y1="45" x2="330" y2="45" stroke="#79c0ff" stroke-width="2" marker-end="url(#arrow760)"/>
  <defs><marker id="arrow760" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker></defs>

  <rect x="340" y="20" width="260" height="50" rx="8" fill="#0f1620" stroke="#79c0ff"/>
  <text x="470" y="50" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">Java 22: standard, no flag needed</text>

  <text x="320" y="120" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">A narrowly scoped syntax addition needed only one preview round to confirm its design</text>
</svg>

*A small, low-risk syntax feature can graduate to standard faster than a larger structural change.*

## 5. Runnable example

Scenario: processing a batch of transaction records where several fields are irrelevant to a given check, using `_` throughout without any preview flag.

### Level 1 — Basic

```java
public class TxCheckBasic {
    record Transaction(String id, double amount, String currency, String status) {}

    public static void main(String[] args) {
        Transaction[] transactions = {
            new Transaction("t1", 100.0, "USD", "completed"),
            new Transaction("t2", 50.0, "USD", "failed"),
        };
        int completedCount = 0;
        for (Transaction tx : transactions) {
            if (tx.status().equals("completed")) {
                completedCount++;
            }
        }
        System.out.println("completed: " + completedCount);
    }
}
```

**How to run:** `java TxCheckBasic.java` (JDK 22+).

This counts completed transactions using every field's real name, even though the loop variable `tx` and several of its fields (`id`, `amount`, `currency`) aren't individually needed for this particular check.

### Level 2 — Intermediate

```java
public class TxCheckUnnamed {
    record Transaction(String id, double amount, String currency, String status) {}

    public static void main(String[] args) {
        Transaction[] transactions = {
            new Transaction("t1", 100.0, "USD", "completed"),
            new Transaction("t2", 50.0, "USD", "failed"),
        };
        int completedCount = 0;
        for (Transaction(_, _, _, var status) : transactions) {
            if (status.equals("completed")) {
                completedCount++;
            }
        }
        System.out.println("completed: " + completedCount);
    }
}
```

**How to run:** `java TxCheckUnnamed.java` (no `--enable-preview` needed on Java 22+).

The real-world concern added: a record pattern destructures each `Transaction` directly in the enhanced `for` loop header, using `_` for the three fields (`id`, `amount`, `currency`) this particular check doesn't need and `var status` for the one it does — making it visually obvious, at the loop declaration itself, which fields this code actually depends on.

### Level 3 — Advanced

```java
import java.util.*;

public class TxCheckAdvanced {
    record Transaction(String id, double amount, String currency, String status) {}

    static Map<String, Double> totalByStatus(List<Transaction> transactions) {
        Map<String, Double> totals = new LinkedHashMap<>();
        for (Transaction(_, var amount, _, var status) : transactions) {
            totals.merge(status, amount, Double::sum);
        }
        return totals;
    }

    public static void main(String[] args) {
        List<Transaction> transactions = List.of(
            new Transaction("t1", 100.0, "USD", "completed"),
            new Transaction("t2", 50.0, "USD", "failed"),
            new Transaction("t3", 75.0, "EUR", "completed"),
            new Transaction("t4", 20.0, "USD", "pending")
        );

        Map<String, Double> totals = totalByStatus(transactions);
        for (var entry : totals.entrySet()) {
            System.out.printf("%s: %.2f%n", entry.getKey(), entry.getValue());
        }

        // `_` as a catch parameter: only whether parsing failed matters, not why
        String[] rawAmounts = {"100.0", "not-a-number", "75.5"};
        int validCount = 0;
        for (String raw : rawAmounts) {
            try {
                Double.parseDouble(raw);
                validCount++;
            } catch (NumberFormatException _) {
                System.out.println("skipping invalid amount: " + raw);
            }
        }
        System.out.println("valid amounts: " + validCount);
    }
}
```

**How to run:** `java TxCheckAdvanced.java`.

This adds the production-flavored hard case: `_` used across **two different constructs** in one program — inside a record pattern in an enhanced `for` loop (discarding `id` and `currency` while keeping `amount` and `status`), and as a `catch` parameter (discarding the specific `NumberFormatException` instance, since only the fact that parsing failed matters) — demonstrating the feature's reach across the language now that it needs no preview flag.

## 6. Walkthrough

Tracing `TxCheckAdvanced.main`:

1. `main` builds a list of four transactions with mixed statuses and currencies, then calls `totalByStatus(transactions)`.
2. Inside `totalByStatus`, the enhanced `for` loop `for (Transaction(_, var amount, _, var status) : transactions)` destructures each `Transaction` as it's iterated: the `id` and `currency` components are matched against `_` (bound to nothing), while `amount` and `status` are bound to `var`-typed locals.
3. For each transaction, `totals.merge(status, amount, Double::sum)` either inserts a new entry for that status or adds `amount` to the existing running total — after all four iterations, `totals` holds `{completed=175.0, failed=50.0, pending=20.0}` (100.0 + 75.0 for the two `"completed"` transactions, since `t1`'s USD and `t3`'s EUR amounts are summed together in this simplified example without currency conversion).
4. Back in `main`, the entries are printed in insertion order (from the `LinkedHashMap`): `completed`, `failed`, `pending`.
5. The second part builds `rawAmounts`, an array mixing valid and invalid numeric strings, and loops over it. For `"100.0"` and `"75.5"`, `Double.parseDouble` succeeds and `validCount` increments. For `"not-a-number"`, `Double.parseDouble` throws `NumberFormatException`, caught by `catch (NumberFormatException _)` — the exception object itself is discarded since the handling logic (printing a skip message) doesn't need any detail from it.
6. `main` prints the final valid count.

Expected output:
```
completed: 175.00
failed: 50.00
pending: 20.00
skipping invalid amount: not-a-number
valid amounts: 2
```

## 7. Gotchas & takeaways

> **Gotcha:** because `_` is no longer available as a real identifier as of Java 21+ (reserved for this unnamed-variable role), any pre-existing code that declared a variable literally named `_` — legal, if unusual, in older Java versions — fails to compile on Java 21 or later and must be renamed. This is the one backward-compatibility cost that made standardizing the feature safe: the ambiguity was resolved before, not after, standardization.

- Standardized in Java 22 (up from a single preview round in Java 21) — no `--enable-preview` flag needed.
- Works in `catch` clauses, lambda parameters, `for` loop variables, and record pattern components — anywhere Java's syntax requires a name that isn't actually needed.
- A single underscore `_` used as a declared identifier is now a compile error — the language reserved it exclusively for this feature.
- Use `_` to make "this value is deliberately unused" visible at the declaration site, improving readability for both human readers and static-analysis tooling.
- See [unnamed classes & instance main methods](0752-unnamed-classes-instance-main-methods-preview.md) for a related, still-previewing Java 21/22 simplification aimed at reducing incidental ceremony.
