---
card: java
gi: 202
slug: static-initializer-blocks
title: Static initializer blocks
---

## 1. What it is

A **static initializer block** is a `static { ... }` block written directly inside a class, used to run setup logic for static fields that's too complex for a simple one-line initializer expression. It runs exactly **once** per class, the first time the class is loaded and initialized by the JVM — before any static method is called, any static field is accessed from outside, or any instance of the class is created — and always before any regular (non-static) construction happens.

```java
class Config {
    static final java.util.Map<String, String> DEFAULTS;

    static { // static initializer block: runs once, when the class is first loaded
        DEFAULTS = new java.util.HashMap<>();
        DEFAULTS.put("timeout", "30");
        DEFAULTS.put("retries", "3");
    }
}

System.out.println(Config.DEFAULTS.get("timeout")); // 30 — the block already ran by the time this executes
```

Building a `Map` with several entries can't be expressed as a single field-initializer expression the way `int x = 5;` can — the static block provides a full block of ordinary code (loops, conditionals, multiple statements) to set up static state that a one-line initializer simply can't express.

## 2. Why & when

Static initializer blocks exist for exactly the situations where static field setup needs more than a single expression:

- **Complex static setup** — populating a lookup table, loading configuration from multiple steps, or computing a value that requires several statements (a loop, a try/catch, conditional logic).
- **Guaranteed one-time execution** — the JVM guarantees a static block runs exactly once, the first time the class is actually used, regardless of how many instances are later created — this is the correct place for setup that should never be repeated.
- **Ordering with multiple static fields** — when several static fields depend on each other in complex ways, a static block lets you sequence their initialization explicitly, with full control, rather than being limited to what individual field-initializer expressions can express.

You reach for a static block specifically when a static field's correct initial value can't be written as one simple expression — for anything a single line can express cleanly (`static final double PI = 3.14159;`), a plain field initializer remains simpler and is generally preferred.

## 3. Core concept

```java
class Registry {
    static final java.util.List<String> KNOWN_CODES = new java.util.ArrayList<>();

    static {
        System.out.println("Static block running..."); // runs exactly once
        for (int i = 1; i <= 3; i++) {
            KNOWN_CODES.add("CODE-" + i);
        }
    }

    Registry() {
        System.out.println("Constructor running"); // runs once PER instance
    }
}

public class StaticBlockDemo {
    public static void main(String[] args) {
        System.out.println("Before first use");
        new Registry(); // triggers class loading -> static block runs FIRST, then the constructor
        new Registry(); // static block does NOT run again; only the constructor runs
        System.out.println(Registry.KNOWN_CODES);
    }
}
```

The output shows `"Static block running..."` printed exactly **once**, before the first `"Constructor running"` line, even though `new Registry()` is called twice — the static block runs only on the class's very first use, while the constructor runs anew for every single `new` call.

## 4. Diagram

<svg viewBox="0 0 600 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A timeline showing the static block running exactly once when the class is first loaded, before any constructor calls, followed by multiple separate constructor executions for each new instance created afterward">
  <rect x="8" y="8" width="584" height="154" rx="8" fill="#0d1117"/>

  <rect x="30" y="40" width="160" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="110" y="65" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">static block (once)</text>

  <line x1="190" y1="60" x2="240" y2="60" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#sb)"/>

  <rect x="240" y="40" width="150" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="315" y="65" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">constructor (call 1)</text>

  <line x1="390" y1="60" x2="440" y2="60" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#sb)"/>

  <rect x="440" y="40" width="150" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="515" y="65" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">constructor (call 2)</text>

  <defs><marker id="sb" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker></defs>

  <text x="300" y="115" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">The static block runs once, on first class use — every "new" call after that only re-runs the constructor.</text>
</svg>

The static block runs exactly once, no matter how many instances are subsequently created.

## 5. Runnable example

Scenario: a simple currency-conversion helper needing a precomputed exchange-rate table — starting with a basic static block populating a lookup table, then extending to handle a setup step that could fail, then hardening into a case demonstrating the "runs exactly once" guarantee concretely, across multiple uses.

### Level 1 — Basic

```java
import java.util.HashMap;
import java.util.Map;

public class CurrencyBasic {
    static final Map<String, Double> RATES = new HashMap<>();

    static {
        RATES.put("USD", 1.0);
        RATES.put("EUR", 0.92);
        RATES.put("GBP", 0.79);
    }

    public static void main(String[] args) {
        System.out.println("1 USD = " + RATES.get("EUR") + " EUR");
    }
}
```

**How to run:** `java CurrencyBasic.java`

The static block populates `RATES` with three entries the moment `CurrencyBasic` is first loaded — by the time `main` runs and reads `RATES.get("EUR")`, the block has already completed, so the lookup succeeds immediately.

### Level 2 — Intermediate

Same currency helper, now with setup logic complex enough to need a loop and a conditional — something a single field-initializer expression genuinely could not express as cleanly.

```java
import java.util.HashMap;
import java.util.Map;

public class CurrencyIntermediate {
    static final Map<String, Double> RATES = new HashMap<>();
    static final String[] CODES = { "USD", "EUR", "GBP", "JPY" };
    static final double[] VALUES = { 1.0, 0.92, 0.79, 149.50 };

    static {
        for (int i = 0; i < CODES.length; i++) {
            if (VALUES[i] > 0) { // a conditional as part of setup — awkward as a single expression
                RATES.put(CODES[i], VALUES[i]);
            }
        }
        System.out.println("Loaded " + RATES.size() + " currency rates");
    }

    public static void main(String[] args) {
        System.out.println("1 USD = " + RATES.get("JPY") + " JPY");
    }
}
```

**How to run:** `java CurrencyIntermediate.java`

The static block's loop and conditional populate `RATES` from two parallel arrays — this kind of multi-step, conditional setup logic is exactly what static blocks are for, since a single field-initializer expression has no natural way to express "loop over these arrays, applying a condition, building up a map."

### Level 3 — Advanced

Same currency helper, now demonstrating concretely that the static block runs only once, even across multiple calls to a static method that "uses" the class — by adding a counter that would reveal repeated execution if it somehow occurred.

```java
import java.util.HashMap;
import java.util.Map;

public class CurrencyAdvanced {
    static final Map<String, Double> RATES = new HashMap<>();
    static int staticBlockRunCount = 0;

    static {
        staticBlockRunCount++; // if this block ran more than once, this would exceed 1
        RATES.put("USD", 1.0);
        RATES.put("EUR", 0.92);
        System.out.println("Static block executed; run count is now " + staticBlockRunCount);
    }

    static double convert(double amount, String currency) {
        Double rate = RATES.get(currency);
        if (rate == null) {
            throw new IllegalArgumentException("Unknown currency: " + currency);
        }
        return amount * rate;
    }

    public static void main(String[] args) {
        System.out.println(convert(100, "EUR"));
        System.out.println(convert(50, "USD"));
        System.out.println(convert(200, "EUR"));

        System.out.println("Final static block run count: " + staticBlockRunCount); // still 1
    }
}
```

**How to run:** `java CurrencyAdvanced.java`

`staticBlockRunCount` is printed once during class loading (with value `1`) and again at the very end of `main` (still `1`) — despite `convert` being called three separate times, each of those calls only *uses* the already-initialized `RATES` map; none of them re-triggers the static block, confirming the JVM's one-time-only guarantee directly through observable program output.

## 6. Walkthrough

Trace `CurrencyAdvanced.main`'s execution from the very start:

**Class loading.** The first reference to `CurrencyAdvanced` (calling `main`) triggers class initialization. The static block runs: `staticBlockRunCount++` makes it `1`; `RATES` gets its two entries; `"Static block executed; run count is now 1"` prints. This happens *before* `main`'s own body begins executing any of its own statements.

**First `convert(100, "EUR")`.** `RATES.get("EUR")` returns `0.92` (already populated by the static block). Returns `100 * 0.92 = 92.0`. Prints `92.0`.

**Second `convert(50, "USD")`.** `RATES.get("USD")` returns `1.0`. Returns `50 * 1.0 = 50.0`. Prints `50.0`.

**Third `convert(200, "EUR")`.** `RATES.get("EUR")` returns `0.92` again (unchanged; the static block never re-ran). Returns `200 * 0.92 = 184.0`. Prints `184.0`.

**Final check.** `staticBlockRunCount` is still `1` — none of the three `convert` calls, nor anything else in `main`, caused the static block to run again.

```
class loading: static block runs once -> staticBlockRunCount = 1, RATES populated
main() begins:
  convert(100, "EUR") -> 100 * 0.92 = 92.0
  convert(50, "USD")  -> 50 * 1.0 = 50.0
  convert(200, "EUR") -> 200 * 0.92 = 184.0
  staticBlockRunCount still 1 (never re-executed)
```

**Final output.** `"Static block executed; run count is now 1"`, then `92.0`, `50.0`, `184.0`, and finally `"Final static block run count: 1"` — five lines total, with the run count confirmed unchanged throughout.

## 7. Gotchas & takeaways

> **A static initializer block runs when the class is first loaded and initialized by the JVM, which can be earlier than you might expect** — merely referencing a `static` field or calling a `static` method can trigger class loading (and therefore the static block), even before any object of that class is ever created with `new`.

> **If a static block throws an uncaught exception, the class fails to initialize entirely, and every subsequent attempt to use it throws `ExceptionInInitializerError`** (wrapping the original exception) for the remainder of the program's run — a failed static block effectively makes the class permanently unusable, which is why static blocks should be written defensively, especially around anything that could fail (file I/O, parsing external configuration, and similar).

- A `static { ... }` block runs exactly once, when the class is first loaded, before any static method call or instance creation.
- Static blocks are for setup logic too complex for a simple field-initializer expression — loops, conditionals, or multiple related statements.
- Multiple `new` calls or repeated static method calls never re-trigger an already-run static block.
- An exception thrown inside a static block prevents the class from initializing at all, breaking every subsequent attempt to use it for the rest of the program.
