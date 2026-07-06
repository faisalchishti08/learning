---
card: java
gi: 265
slug: multiple-catch-blocks-ordering
title: Multiple catch blocks & ordering
---

## 1. What it is

A single `try` block can be followed by any number of `catch` blocks, each targeting a different exception type, and Java checks them strictly in the order they are written, from top to bottom. The moment a matching clause is found, its body runs and every subsequent `catch` clause for that same `try` is skipped entirely — this makes the *order* in which you write multiple `catch` blocks a meaningful, compiler-enforced part of the program's behaviour, not just a stylistic choice.

```java
public class MultipleCatchDemo {
    public static void main(String[] args) {
        try {
            Object[] items = new String[3];
            items[0] = 42; // throws ArrayStoreException: an int cannot go in a String[]
        } catch (ArrayStoreException e) {          // most specific relevant type first
            System.out.println("Array store problem: " + e.getMessage());
        } catch (RuntimeException e) {              // broader: catches any OTHER unchecked exception
            System.out.println("Some other runtime problem: " + e.getMessage());
        } catch (Exception e) {                       // broadest: a final safety net
            System.out.println("Unexpected checked exception: " + e.getMessage());
        }
    }
}
```

Three `catch` clauses are stacked from most specific (`ArrayStoreException`) to least specific (`Exception`); the thrown `ArrayStoreException` matches the first clause exactly, so its body runs and the other two clauses are never even evaluated for this particular exception.

## 2. Why & when

Ordering multiple `catch` blocks correctly matters because Java's matching is based on the exception hierarchy (covered in earlier topics), and a broader type placed too early would "steal" exceptions that a narrower, more specific clause further down was meant to handle.

- **Most specific to least specific is required, not just conventional** — since `catch` matching uses "is-a" polymorphism, a broader type like `Exception` matches everything a narrower type like `IllegalArgumentException` would also match; if the broader clause came first, the narrower one would never run, and Java's compiler actively detects and rejects this exact situation as an "already caught" error.
- **Layering handling from precise to general** — a common, effective pattern is to catch a small number of specific exception types you have distinct, tailored responses for, followed by a broader catch-all (often `Exception`) as a safety net for anything unanticipated — this lets you handle the cases you understand precisely while still gracefully catching genuine surprises.
- **Avoiding one giant, unfocused catch clause** — rather than writing one `catch (Exception e)` block with internal `if (e instanceof X)` checks to differentiate behaviour, multiple ordered `catch` clauses let the language itself do the dispatching, producing clearer, more maintainable code.

Write multiple `catch` clauses whenever a single `try` block can fail in several genuinely different ways that warrant different responses; always order them from most specific to least specific, and reserve a final, broad `catch (Exception e)` (if you include one at all) purely as a safety net for cases you did not specifically anticipate.

## 3. Core concept

```java
public class MultipleCatchCore {
    static int process(String input, int[] data) {
        int index = Integer.parseInt(input);
        return data[index];
    }

    public static void main(String[] args) {
        try {
            System.out.println(process("abc", new int[]{1, 2, 3}));
        } catch (NumberFormatException e) {              // most specific: a parsing problem
            System.out.println("Bad number format: " + e.getMessage());
        } catch (ArrayIndexOutOfBoundsException e) {      // a different, unrelated specific problem
            System.out.println("Bad index: " + e.getMessage());
        } catch (RuntimeException e) {                      // broader safety net for anything else unchecked
            System.out.println("Other runtime issue: " + e.getMessage());
        }
    }
}
```

Even though `NumberFormatException` and `ArrayIndexOutOfBoundsException` are unrelated to each other (neither is a subtype of the other), both are subtypes of `RuntimeException`, so that third, broader clause is correctly placed last — it will only ever run for some *other* `RuntimeException` subtype that isn't one of the two more specific cases already handled above it.

## 4. Diagram

<svg viewBox="0 0 600 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Multiple catch clauses are checked top to bottom, ordered from most specific type to least specific, the compiler rejects a broader clause placed before a narrower one it would already match">
  <rect x="8" y="8" width="584" height="184" rx="8" fill="#0d1117"/>

  <rect x="60" y="20" width="240" height="30" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="180" y="40" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">catch (NumberFormatException e)</text>

  <rect x="60" y="60" width="240" height="30" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="180" y="80" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">catch (ArrayIndexOutOfBoundsException e)</text>

  <rect x="60" y="100" width="240" height="30" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="180" y="120" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">catch (RuntimeException e) — broader</text>

  <text x="450" y="45" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Checked top to bottom.</text>
  <text x="450" y="63" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">First match wins,</text>
  <text x="450" y="81" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">rest are skipped.</text>

  <text x="300" y="160" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">Reversing this order (broad type first) is a COMPILE ERROR: "already caught".</text>
</svg>

`catch` clauses are checked top to bottom; ordering from specific to general is required by the compiler.

## 5. Runnable example

Scenario: a small batch-processing routine handling several distinct failure categories, evolved from two catch clauses into a fully layered set demonstrating precise, ordered dispatch across genuinely different exception types.

### Level 1 — Basic

```java
public class MultipleCatchBasic {
    public static void main(String[] args) {
        String[] inputs = { "42", "abc" };
        for (String input : inputs) {
            try {
                System.out.println("Parsed: " + Integer.parseInt(input));
            } catch (NumberFormatException e) {
                System.out.println("Not a number: " + input);
            }
        }
    }
}
```

**How to run:** `java MultipleCatchBasic.java`

Only one exception type can actually be thrown here, so a single `catch` clause suffices — this is the baseline before more failure modes are introduced.

### Level 2 — Intermediate

Same batch idea, now processing entries that can fail in two genuinely different ways, with two ordered `catch` clauses giving each its own tailored message.

```java
public class MultipleCatchIntermediate {
    static int[] inventory = { 10, 20, 30 };

    static int lookupQuantity(String indexStr) {
        int index = Integer.parseInt(indexStr); // can throw NumberFormatException
        return inventory[index];                  // can throw ArrayIndexOutOfBoundsException
    }

    public static void main(String[] args) {
        String[] requests = { "1", "abc", "10" };
        for (String req : requests) {
            try {
                System.out.println("Quantity: " + lookupQuantity(req));
            } catch (NumberFormatException e) {
                System.out.println("Invalid index format '" + req + "': " + e.getMessage());
            } catch (ArrayIndexOutOfBoundsException e) {
                System.out.println("Index out of range '" + req + "': " + e.getMessage());
            }
        }
    }
}
```

**How to run:** `java MultipleCatchIntermediate.java`

`NumberFormatException` and `ArrayIndexOutOfBoundsException` are unrelated exception types (neither extends the other), so their relative order between each other doesn't matter for correctness — but both must still be more specific than any broader catch that might follow them, which the next level demonstrates.

### Level 3 — Advanced

Same inventory system, now with a third, more specific custom exception layered in above a broad `RuntimeException` safety net, demonstrating the complete, correctly-ordered hierarchy: two unrelated specific types, a domain-specific custom type, and a catch-all — in an order the compiler accepts.

```java
public class MultipleCatchAdvanced {
    static class OutOfStockException extends RuntimeException { // a domain-specific unchecked exception
        OutOfStockException(String message) { super(message); }
    }

    static int[] inventory = { 0, 20, 30 }; // index 0 is out of stock

    static int lookupQuantity(String indexStr) {
        int index = Integer.parseInt(indexStr);       // NumberFormatException possible
        int quantity = inventory[index];                 // ArrayIndexOutOfBoundsException possible
        if (quantity == 0) throw new OutOfStockException("item at index " + index + " is out of stock");
        return quantity;
    }

    public static void main(String[] args) {
        String[] requests = { "1", "abc", "10", "0" };
        for (String req : requests) {
            try {
                System.out.println("Quantity: " + lookupQuantity(req));
            } catch (OutOfStockException e) {                   // MOST specific: our own custom type
                System.out.println("Out of stock: " + e.getMessage());
            } catch (NumberFormatException e) {                   // specific: a different unrelated type
                System.out.println("Invalid index format '" + req + "': " + e.getMessage());
            } catch (ArrayIndexOutOfBoundsException e) {           // specific: another unrelated type
                System.out.println("Index out of range '" + req + "': " + e.getMessage());
            } catch (RuntimeException e) {                          // BROADEST: safety net, must be LAST
                System.out.println("Unexpected problem: " + e.getMessage());
            }
        }
    }
}
```

**How to run:** `java MultipleCatchAdvanced.java`

`OutOfStockException`, `NumberFormatException`, and `ArrayIndexOutOfBoundsException` are all unrelated to each other but all extend `RuntimeException`, so the final `catch (RuntimeException e)` clause must come last — placing it any earlier would make the compiler reject the program, since it would make one or more of the specific clauses below it permanently unreachable.

## 6. Walkthrough

Trace the loop in `MultipleCatchAdvanced.main` over all four requests.

**`req = "1"`.** `lookupQuantity("1")`: `Integer.parseInt("1")` succeeds, `index = 1`. `inventory[1]` is `20` (valid index, non-zero quantity). `quantity == 0` is `false`, so `20` is returned normally. Prints `"Quantity: 20"`. No exception, so no `catch` clause runs.

**`req = "abc"`.** `lookupQuantity("abc")`: `Integer.parseInt("abc")` throws `NumberFormatException` immediately. Java checks the `catch` clauses top to bottom: `OutOfStockException`? No match (wrong type entirely). `NumberFormatException`? Match — runs this clause. Prints `"Invalid index format 'abc': For input string: \"abc\""`.

**`req = "10"`.** `lookupQuantity("10")`: `Integer.parseInt("10")` succeeds, `index = 10`. `inventory[10]` throws `ArrayIndexOutOfBoundsException`, since `inventory` only has indices `0` through `2`. Checking clauses: `OutOfStockException`? No. `NumberFormatException`? No. `ArrayIndexOutOfBoundsException`? Match — runs this clause. Prints `"Index out of range '10': Index 10 out of bounds for length 3"`.

**`req = "0"`.** `lookupQuantity("0")`: `Integer.parseInt("0")` succeeds, `index = 0`. `inventory[0]` is `0` (a valid index, but the quantity itself is zero). `quantity == 0` is `true`, so `OutOfStockException("item at index 0 is out of stock")` is thrown. Checking clauses: `OutOfStockException`? Match immediately (it's the very first clause, and it's an exact type match). Prints `"Out of stock: item at index 0 is out of stock"`.

```
"1"   -> parses ok, inventory[1]=20, quantity!=0 -> returns 20 -> "Quantity: 20"
"abc" -> NumberFormatException -> matches 1st applicable clause (NumberFormatException) -> "Invalid index format..."
"10"  -> parses ok, inventory[10] throws AIOOBE -> matches ArrayIndexOutOfBoundsException clause -> "Index out of range..."
"0"   -> parses ok, inventory[0]=0, quantity==0 -> throws OutOfStockException -> matches FIRST clause -> "Out of stock..."
```

**Final output.**
```
Quantity: 20
Invalid index format 'abc': For input string: "abc"
Index out of range '10': Index 10 out of bounds for length 3
Out of stock: item at index 0 is out of stock
```
Notice the broad `catch (RuntimeException e)` safety net never actually runs in this program at all — every exception that occurred was more precisely matched by one of the three specific clauses above it, exactly as intended when ordering from specific to general.

## 7. Gotchas & takeaways

> **Placing a broader exception type before a narrower one it would also match is a compile error, not just bad style** — Java's compiler statically analyzes the catch chain and rejects any clause it can prove is unreachable because an earlier, broader clause would always catch it first; the exact error message typically reads something like "exception X has already been caught."

> **Unrelated exception types (like `NumberFormatException` and `ArrayIndexOutOfBoundsException`, neither of which extends the other) can be ordered in either relative sequence without a compile error** — the strict ordering requirement only applies between a type and its actual supertypes; two "sibling" exception types with no inheritance relationship to each other impose no ordering constraint between themselves, only relative to any broader common supertype that might also be caught.

- Multiple `catch` clauses attached to one `try` block are checked strictly top to bottom; the first matching clause runs, and all others are skipped for that exception.
- Order clauses from most specific to least specific — the compiler enforces this and rejects an unreachable, overly broad clause placed too early.
- A layered set of catches (specific custom exceptions, then specific JDK exceptions, then a broad safety net) lets you handle known failure modes precisely while still catching genuine surprises.
- Unrelated exception types with no inheritance relationship between them can be ordered freely relative to each other; only the specific-before-general rule relative to actual supertypes is enforced.
