---
card: java
gi: 112
slug: compound-assignment
title: Compound assignment (+= -= *= /= %= &= |= ^= <<= >>= >>>=)
---

## 1. What it is

Compound assignment operators combine a binary operator with `=` into one shorthand: `x += y` means "compute `x + y`, then store the result back into `x`" — but with one crucial difference from writing it out longhand. Java's specification (JLS §15.26.2) says `x op= y` is equivalent to `x = (T) (x op y)`, where `T` is `x`'s declared type — an **implicit cast back to `x`'s type** is inserted automatically. This means compound assignment can silently narrow a value in a way that the equivalent longhand expression would refuse to compile.

```java
byte b = 10;
b += 5;             // legal: implicitly equivalent to b = (byte) (b + 5)
// b = b + 5;       // would NOT compile: int cannot be assigned to byte without an explicit cast

int i = 10;
i *= 1.5;            // legal: implicitly equivalent to i = (int) (i * 1.5), silently truncates to 15
// i = i * 1.5;      // would NOT compile: double cannot be assigned to int without a cast
```

The full set: `+=`, `-=`, `*=`, `/=`, `%=` (arithmetic), `&=`, `|=`, `^=` (bitwise/logical), and `<<=`, `>>=`, `>>>=` (shift) — all follow the same "implicit cast back to the left operand's type" rule.

## 2. Why & when

Compound assignment is used constantly for accumulators, counters, flag manipulation, and in-place updates:

- Accumulating totals: `total += price;`
- Scaling in place: `balance *= (1 + interestRate);`
- Setting/clearing bit flags: `permissions |= WRITE_FLAG;` / `permissions &= ~WRITE_FLAG;`
- Shifting in place: `hash = (hash << 5) - hash + c;` style rolling hash updates (though this specific one uses `=` not `<<=`, plain shift-assign like `mask <<= 1;` is common for bit-scanning loops).

The danger is exactly the implicit-cast convenience: because `x op= y` compiles even when `x = x op y` would not, it is easy to accidentally narrow a value without realizing it — for example, accumulating `double` amounts into an `int` total via `+=` silently truncates every addition, whereas the longhand form would have forced the programmer to notice the type mismatch at compile time.

## 3. Core concept

```java
public class CompoundAssignmentDemo {
    public static void main(String[] args) {
        // Arithmetic compound assignment
        int total = 100;
        total += 50;    // total = 150
        total -= 30;    // total = 120
        total *= 2;      // total = 240
        total /= 4;      // total = 60
        total %= 7;      // total = 4
        System.out.println("total after chain: " + total);

        // The implicit narrowing cast that += hides
        byte b = 10;
        b += 5;           // legal — implicit (byte) cast inserted automatically
        System.out.println("b = " + b);

        int i = 10;
        i *= 1.5;          // legal — implicit (int) cast, silently truncates 15.0 to 15
        System.out.println("i *= 1.5 -> " + i);

        // Bitwise/logical compound assignment
        int permissions = 0b0001;      // READ only
        int WRITE = 0b0010, EXEC = 0b0100;
        permissions |= WRITE;           // set the WRITE bit
        permissions |= EXEC;            // set the EXEC bit
        System.out.println("permissions: " + Integer.toBinaryString(permissions));  // 111
        permissions &= ~WRITE;           // clear the WRITE bit
        System.out.println("after clearing WRITE: " + Integer.toBinaryString(permissions));  // 101

        // Shift compound assignment
        int mask = 1;
        mask <<= 3;    // mask = 1 << 3 = 8
        System.out.println("mask after <<= 3: " + mask);
    }
}
```

## 4. Diagram

<svg viewBox="0 0 700 175" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Compound assignment hidden cast diagram: byte b plus equals 5 is equivalent to b equals open paren byte close paren of b plus 5, with an implicit cast inserted automatically that the longhand form would not allow without an explicit cast.">
  <rect x="8" y="8" width="684" height="159" rx="8" fill="#0d1117"/>
  <text x="350" y="24" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">x op= y  is really  x = (T) (x op y) — the cast to T is IMPLICIT</text>

  <rect x="16" y="34" width="330" height="118" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="181" y="52" fill="#6db33f" font-size="8.5" text-anchor="middle" font-family="sans-serif">Compound form — compiles fine</text>
  <text x="30" y="74" fill="#e6edf3" font-size="9" font-family="monospace">byte b = 10;</text>
  <text x="30" y="92" fill="#e6edf3" font-size="9" font-family="monospace">b += 5;</text>
  <text x="30" y="112" fill="#79c0ff" font-size="8" font-family="monospace">≡ b = (byte)(b + 5);</text>
  <text x="30" y="132" fill="#6db33f" font-size="7.5" font-family="sans-serif">Implicit cast inserted automatically.</text>

  <rect x="356" y="34" width="328" height="118" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="520" y="52" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">Longhand form — compile ERROR</text>
  <text x="370" y="74" fill="#e6edf3" font-size="9" font-family="monospace">byte b = 10;</text>
  <text x="370" y="92" fill="#e6edf3" font-size="9" font-family="monospace">b = b + 5;</text>
  <text x="370" y="112" fill="#8b949e" font-size="8" font-family="monospace">// int cannot convert to byte</text>
  <text x="370" y="132" fill="#8b949e" font-size="7.5" font-family="sans-serif">Requires an EXPLICIT (byte) cast.</text>
</svg>

The exact same intent, `byte + int`, compiles silently with `+=` but requires an explicit cast when written out longhand.

## 5. Runnable example

Scenario: a simple bank-account balance tracker that applies deposits, withdrawals, and interest — showing where compound assignment's hidden cast is convenient, and where it hides a real bug when mixing `int` cents with `double` interest rates.

### Level 1 — Basic

```java
public class BankBasic {
    public static void main(String[] args) {
        int balanceCents = 10_000;  // $100.00

        balanceCents += 5_000;      // deposit $50.00
        balanceCents -= 2_500;      // withdraw $25.00
        System.out.println("Balance after deposit/withdrawal: " + balanceCents + " cents");

        // Applying "interest" using a double rate directly on the int balance
        balanceCents *= 1.02;       // legal due to implicit cast, but silently truncates
        System.out.println("Balance after 2% interest: " + balanceCents + " cents");
    }
}
```

**How to run:** `java BankBasic.java`

`balanceCents *= 1.02` is legal only because compound assignment inserts an implicit `(int)` cast: it is really `balanceCents = (int) (balanceCents * 1.02)`. The multiplication produces a `double` (e.g., `12750.0 * 1.02 = 13005.0`), and the implicit cast truncates any fractional cents that this particular calculation happens not to have — but for other starting balances, this silently drops fractional cents every time interest is applied, a real bug in financial code that the compiler never flags because `*=` legalizes the narrowing.

### Level 2 — Intermediate

Same tracker, now making the truncation explicit and intentional (rounding properly instead of silently truncating), and demonstrating the compile error that occurs if you try to remove the implicit cast by switching to the longhand form.

```java
public class BankIntermediate {
    public static void main(String[] args) {
        int balanceCents = 10_000;

        balanceCents += 5_000;
        balanceCents -= 2_500;
        System.out.println("Balance: " + balanceCents + " cents");

        // Explicit, intentional rounding instead of relying on the implicit truncating cast
        double afterInterest = balanceCents * 1.02;
        balanceCents = (int) Math.round(afterInterest);   // rounds to nearest cent, not truncates
        System.out.println("Balance after 2% interest (rounded): " + balanceCents + " cents");

        // If you tried: balanceCents = balanceCents * 1.02;  <- this would NOT compile:
        // error: incompatible types: possible lossy conversion from double to int
        // Compound assignment (*=) hides exactly this error by inserting an implicit cast.
    }
}
```

**How to run:** `java BankIntermediate.java`

Instead of relying on `*=`'s implicit truncating cast, the interest calculation is now split into two explicit steps: compute `afterInterest` as a full-precision `double`, then convert it back to `int` cents using `Math.round`, which rounds to the *nearest* cent rather than always truncating toward zero. This produces a more financially sensible result and, more importantly, makes the precision-loss step visible and intentional in the code rather than hidden inside a `*=`.

### Level 3 — Advanced

Same bank tracker, now managing account permission flags with bitwise compound assignment (`|=`, `&=`, `^=`), and demonstrating a subtle interaction between compound assignment and array/field access, where the left-hand side is only evaluated once even though it appears conceptually on both sides of the operation.

```java
public class BankAdvanced {

    static final int READ = 0b0001, WRITE = 0b0010, TRANSFER = 0b0100, ADMIN = 0b1000;

    static int[] accountPermissions = new int[3];  // one permission bitmask per account
    static int callCount = 0;

    static int accountIndexWithSideEffect() {
        callCount++;   // simulate an expensive/side-effecting lookup, e.g., logging or a cache check
        return 1;       // always targets account index 1 for this demo
    }

    public static void main(String[] args) {
        accountPermissions[0] = READ | WRITE;

        // Grant TRANSFER permission to account 1, using a side-effecting index expression
        accountPermissions[accountIndexWithSideEffect()] |= TRANSFER;
        System.out.println("Index lookup called " + callCount + " time(s)");  // exactly 1, not 2!
        System.out.println("Account 1 permissions: " + Integer.toBinaryString(accountPermissions[1]));

        // Toggle ADMIN on account 0 with ^= (flips the bit: off->on, on->off)
        accountPermissions[0] ^= ADMIN;
        System.out.println("Account 0 after toggling ADMIN on:  " + Integer.toBinaryString(accountPermissions[0]));
        accountPermissions[0] ^= ADMIN;
        System.out.println("Account 0 after toggling ADMIN off: " + Integer.toBinaryString(accountPermissions[0]));

        // Revoke WRITE from account 0 using &= ~FLAG, the standard "clear a bit" idiom
        accountPermissions[0] &= ~WRITE;
        System.out.println("Account 0 after revoking WRITE: " + Integer.toBinaryString(accountPermissions[0]));
    }
}
```

**How to run:** `java BankAdvanced.java`

`accountPermissions[accountIndexWithSideEffect()] |= TRANSFER` looks like it might evaluate `accountIndexWithSideEffect()` twice (once to read the current value, once to write the new one) — but the JLS guarantees the left-hand side's array/field access expression is evaluated only **once**, and its result (the array reference plus the computed index) is reused for both the read and the write. This is confirmed by `callCount` remaining `1` after the operation, not `2`. `^=` with `ADMIN` demonstrates the standard "toggle a bit" idiom: XOR-ing a bit with `1` flips it, so applying `^= ADMIN` twice in a row restores the original value — useful for switches that need to alternate state. `&= ~WRITE` is the standard "clear a specific bit" idiom: `~WRITE` has every bit set except the `WRITE` bit, so AND-ing with it forces that one bit to `0` while leaving every other bit unchanged.

## 6. Walkthrough

Trace `accountPermissions[accountIndexWithSideEffect()] |= TRANSFER` step by step, given `accountPermissions[1]` starts at `0` (default int array value):

**Evaluate the left-hand side's array reference and index, once.** The JVM evaluates `accountPermissions` (the array reference) and calls `accountIndexWithSideEffect()` exactly one time to get the index, `1`. This single evaluation's results — "the array `accountPermissions`, at index `1`" — are cached for the remainder of this compound operation. `callCount` becomes `1`.

**Read the current value at that location.** Using the cached array-and-index, the JVM reads `accountPermissions[1]`, which is `0`.

**Compute the OR.** `0 | TRANSFER` (where `TRANSFER = 0b0100`) computes `0b0100`.

**Write back, using the same cached location.** The JVM writes `0b0100` back to `accountPermissions[1]`, using the *same* cached array-and-index from step 1 — `accountIndexWithSideEffect()` is **not** called again for this write.

```
accountPermissions[accountIndexWithSideEffect()] |= TRANSFER

Step 1: evaluate index expression ONCE -> callCount=1, index=1  (cached)
Step 2: read accountPermissions[1] -> 0b0000
Step 3: compute 0b0000 | 0b0100 -> 0b0100
Step 4: write 0b0100 to accountPermissions[1]  (using the CACHED index, no second call)
```

**Why this matters.** If the left-hand side's index expression *were* evaluated twice — once for the read, once for the write — and that expression had a side effect that could return a *different* value the second time (e.g., an incrementing counter used as an index), the read and write could target two different array slots, corrupting the operation. The JLS's "evaluate the left-hand side once" rule is what makes compound assignment on array elements and object fields safe to use even when computing the target location is non-trivial or side-effecting.

## 7. Gotchas & takeaways

> **`x op= y` inserts an implicit cast back to `x`'s type — even when the longhand `x = x op y` would fail to compile.** This makes it easy to silently narrow a value (e.g., `int i; i *= 1.5;` truncates) without any compiler warning. When precision loss is possible, prefer writing the cast explicitly and separately so the narrowing is visible in the code.

> **The left-hand side of a compound assignment on an array element or object field is evaluated exactly once**, even though conceptually the same location is both read and written. A side-effecting index expression only runs once, not twice — this guarantee is what makes patterns like `arr[computeIndex()] += 1` safe.

- Compound assignment operators exist for arithmetic (`+= -= *= /= %=`), bitwise/logical (`&= |= ^=`), and shifts (`<<= >>= >>>=`) — all insert an implicit cast back to the left operand's declared type.
- Because the implicit cast legalizes narrowing that the longhand form would reject, be deliberate about precision loss in compound assignment, especially with mixed `int`/`double` arithmetic.
- `|=` sets bits, `&= ~flag` clears bits, and `^=` toggles bits — the standard idioms for bitmask manipulation.
- The left-hand side's target location (array index or field) is computed only once per compound assignment, safe even for side-effecting index expressions.
