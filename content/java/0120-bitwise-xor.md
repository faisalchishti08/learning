---
card: java
gi: 120
slug: bitwise-xor
title: Bitwise XOR ^
---

## 1. What it is

`^` computes the **exclusive OR** of its operands. On integer types, each output bit is `1` if the corresponding input bits *differ* (one is `0` and the other is `1`), and `0` if they are the *same* (both `0` or both `1`). On `boolean` operands, `^` computes `true` if exactly one operand is `true` (equivalent to "not equal" for booleans) — and unlike `&&`/`||`, `^` has no meaningful short-circuit form at all, because the result always genuinely depends on both operands; there is no way to determine the outcome from only one side.

```java
int a = 0b1100;   // 12
int b = 0b1010;   // 10
int result = a ^ b;   // 0b0110 = 6 — 1 where the bits DIFFER
System.out.println(result);

boolean x = true, y = false;
System.out.println(x ^ y);   // true — exactly one is true

int n = 5;
System.out.println(n ^ n);    // 0 — XOR-ing anything with itself always gives 0
System.out.println(n ^ 0);     // 5 — XOR-ing with 0 always gives back the original value unchanged
```

Two properties make `^` distinctive among the bitwise operators: `x ^ x == 0` for any `x`, and `x ^ 0 == x` for any `x`. Combined, these make `^` **its own inverse**: applying the same XOR operation twice with the same key cancels out and restores the original value — `(a ^ key) ^ key == a`, always.

## 2. Why & when

`^`'s self-inverse property makes it useful in a specific, recognizable set of situations:

- Toggling a bit flag: `flags ^= BIT` flips that one bit on if it was off, or off if it was on — the standard "toggle" idiom, unlike `|=` (always sets) or `&= ~BIT` (always clears).
- A simple (not cryptographically secure) obfuscation/encoding scheme: `encoded = data ^ key; decoded = encoded ^ key;` recovers the original data because the two XORs with the same key cancel out.
- Detecting which bits differ between two values: `a ^ b` produces a mask showing exactly where `a` and `b` disagree, useful in checksums, error-detection codes, and Gray code sequences.
- The classic (though rarely necessary in modern code) "swap two variables without a temporary" trick, shown in the walkthrough below — mostly of historical/educational interest today, since a plain temporary variable is clearer and no slower.

## 3. Core concept

```java
public class BitwiseXorDemo {
    public static void main(String[] args) {
        int a = 0b1100;  // 12
        int b = 0b1010;  // 10
        System.out.println("a ^ b = " + (a ^ b) + " (binary: " + Integer.toBinaryString(a ^ b) + ")");  // 6, "110"

        // Self-inverse properties
        int n = 42;
        System.out.println("n ^ n = " + (n ^ n));   // 0 — always
        System.out.println("n ^ 0 = " + (n ^ 0));    // 42 — always, unchanged

        // Toggling a bit flag
        int flags = 0b0101;
        int BIT = 0b0010;
        flags ^= BIT;   // toggle bit 1: it was 0, now becomes 1
        System.out.println("After first toggle:  " + Integer.toBinaryString(flags));   // "111"
        flags ^= BIT;    // toggle again: back to 0
        System.out.println("After second toggle: " + Integer.toBinaryString(flags));   // "101"

        // Simple XOR "encoding" (NOT secure encryption, just a demonstration of the cancel property)
        int data = 0b11001010;
        int key = 0b10101010;
        int encoded = data ^ key;
        int decoded = encoded ^ key;   // XOR-ing with the same key again cancels it out
        System.out.println("Original: " + Integer.toBinaryString(data));
        System.out.println("Encoded:  " + Integer.toBinaryString(encoded));
        System.out.println("Decoded:  " + Integer.toBinaryString(decoded));    // matches original
    }
}
```

## 4. Diagram

<svg viewBox="0 0 700 155" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Bitwise XOR diagram: 12 in binary 1100 XOR 10 in binary 1010, computed bit by bit, gives 0110 which is 6. A 1 appears exactly where the two input bits differ.">
  <rect x="8" y="8" width="684" height="139" rx="8" fill="#0d1117"/>
  <text x="350" y="24" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">0b1100 (12) ^ 0b1010 (10) — bit by bit, right to left</text>

  <text x="200" y="52" fill="#e6edf3" font-size="14" text-anchor="middle" font-family="monospace">1  1  0  0</text>
  <text x="200" y="74" fill="#e6edf3" font-size="14" text-anchor="middle" font-family="monospace">1  0  1  0</text>
  <line x1="130" y1="82" x2="270" y2="82" stroke="#8b949e" stroke-width="1.5"/>
  <text x="200" y="100" fill="#6db33f" font-size="14" text-anchor="middle" font-family="monospace">0  1  1  0</text>
  <text x="200" y="122" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">= 6 (1 wherever the two bits DIFFER)</text>

  <text x="500" y="52" fill="#8b949e" font-size="9" font-family="monospace">bit 3: 1 ^ 1 = 0 (same)</text>
  <text x="500" y="70" fill="#8b949e" font-size="9" font-family="monospace">bit 2: 1 ^ 0 = 1 (differ)</text>
  <text x="500" y="88" fill="#8b949e" font-size="9" font-family="monospace">bit 1: 0 ^ 1 = 1 (differ)</text>
  <text x="500" y="106" fill="#8b949e" font-size="9" font-family="monospace">bit 0: 0 ^ 0 = 0 (same)</text>
</svg>

`^` computes each output bit independently — a `1` appears exactly where the two inputs disagree at that position.

## 5. Runnable example

Scenario: a lightweight game-state toggling system (day/night cycle, paused/running flags) that uses `^=` for toggling, extended to a simple XOR-based data obfuscation utility, and finally to a checksum-style "detect which fields changed" comparator.

### Level 1 — Basic

```java
public class ToggleBasic {
    public static void main(String[] args) {
        boolean isPaused = false;

        isPaused ^= true;   // toggling with XOR: false ^ true = true
        System.out.println("After first toggle:  " + isPaused);   // true

        isPaused ^= true;    // toggling again flips it back
        System.out.println("After second toggle: " + isPaused);    // false

        // The same idiom on an int flag bitmask
        int gameFlags = 0b01;   // bit 0 = DAY (currently daytime)
        int DAY_NIGHT_BIT = 0b01;
        gameFlags ^= DAY_NIGHT_BIT;   // day becomes night
        System.out.println("Flags after day->night: " + Integer.toBinaryString(gameFlags));  // "0"
    }
}
```

**How to run:** `java ToggleBasic.java`

`isPaused ^= true` is equivalent to `isPaused = isPaused ^ true`; since XOR-ing any boolean with `true` always flips it (`false ^ true = true`, `true ^ true = false`), this is a clean, self-documenting toggle idiom — `^= true` reads naturally as "flip this flag." The integer version does the same thing at the bit level: `gameFlags ^ DAY_NIGHT_BIT` flips exactly that one bit, leaving any other bits in `gameFlags` untouched (since XOR-ing with `0` in those other positions is a no-op).

### Level 2 — Intermediate

Same toggling idiom applied to multiple independent flags at once, and a simple (explicitly non-cryptographic) XOR obfuscation utility for hiding a numeric game-save value from casual inspection, demonstrating the encode/decode symmetry.

```java
public class ToggleIntermediate {
    static final int DAY_NIGHT = 0b0001, PAUSED = 0b0010, MUTED = 0b0100;

    public static void main(String[] args) {
        int flags = DAY_NIGHT | MUTED;   // starts: daytime, muted, not paused
        System.out.println("Start:  " + Integer.toBinaryString(flags));

        flags ^= PAUSED;                  // pause the game
        System.out.println("Pause:  " + Integer.toBinaryString(flags));

        flags ^= DAY_NIGHT | MUTED;        // toggle BOTH day/night and muted in one operation
        System.out.println("Toggle both: " + Integer.toBinaryString(flags));   // day/night -> night, muted -> unmuted

        // Simple XOR obfuscation of a save-game score value
        int realScore = 152_340;
        int obfuscationKey = 0xABCD1234;
        int storedValue = realScore ^ obfuscationKey;   // what actually gets written to the save file
        System.out.println("Stored (obfuscated): " + storedValue);

        int recoveredScore = storedValue ^ obfuscationKey;   // XOR-ing with the same key again undoes it
        System.out.println("Recovered score: " + recoveredScore + " (matches original? " + (recoveredScore == realScore) + ")");
    }
}
```

**How to run:** `java ToggleIntermediate.java`

`flags ^= PAUSED` toggles just the `PAUSED` bit, leaving `DAY_NIGHT` and `MUTED` untouched, because XOR-ing a bit position with `0` (as `PAUSED`'s mask has in those other positions) never changes it. `flags ^= DAY_NIGHT | MUTED` demonstrates toggling *two* flags simultaneously in one operation: the combined mask `DAY_NIGHT | MUTED` has `1`s in exactly those two bit positions, so XOR-ing with it flips both bits at once while leaving `PAUSED`'s bit alone. The obfuscation example directly exploits `^`'s self-inverse property: `storedValue ^ obfuscationKey` equals `(realScore ^ obfuscationKey) ^ obfuscationKey`, and because `x ^ key ^ key == x` for any `x` and `key` (the two XORs with the same key cancel exactly), `recoveredScore` is guaranteed to equal `realScore` — this is a trivially reversible obfuscation, not real encryption, since anyone who guesses or discovers the key can reverse it instantly, but it is enough to deter casual tampering with a save file opened in a plain text/hex editor.

### Level 3 — Advanced

Same game-state system, now using XOR to build a **change-detection checksum**: comparing two game-state snapshots to find exactly which flags changed between them (a real, common technique in networked/replicated state synchronization), and demonstrating the classic (educational) "swap without a temporary variable" trick as a self-contained example of the `x ^ x == 0` and `x ^ 0 == x` identities working together.

```java
public class ToggleAdvanced {
    static final int DAY_NIGHT = 0b0001, PAUSED = 0b0010, MUTED = 0b0100, GOD_MODE = 0b1000;
    static final String[] FLAG_NAMES = { "DAY_NIGHT", "PAUSED", "MUTED", "GOD_MODE" };
    static final int[] FLAG_BITS = { DAY_NIGHT, PAUSED, MUTED, GOD_MODE };

    static void printChangedFlags(int before, int after) {
        int changed = before ^ after;   // a 1 bit here means that flag differs between snapshots
        System.out.print("Changed flags: ");
        boolean any = false;
        for (int i = 0; i < FLAG_BITS.length; i++) {
            if ((changed & FLAG_BITS[i]) != 0) {
                boolean wasOn = (before & FLAG_BITS[i]) != 0;
                System.out.print(FLAG_NAMES[i] + "(" + wasOn + "->" + !wasOn + ") ");
                any = true;
            }
        }
        if (!any) System.out.print("none");
        System.out.println();
    }

    public static void main(String[] args) {
        int stateBefore = DAY_NIGHT | MUTED;
        int stateAfter  = PAUSED | MUTED | GOD_MODE;

        printChangedFlags(stateBefore, stateAfter);

        // Classic educational trick: swap two ints using only XOR, no temporary variable
        int x = 17, y = 42;
        System.out.println("Before swap: x=" + x + ", y=" + y);
        x = x ^ y;   // x now holds the XOR of both original values
        y = x ^ y;   // y = (origX ^ origY) ^ origY = origX  (origY cancels out)
        x = x ^ y;   // x = (origX ^ origY) ^ origX = origY  (origX cancels out)
        System.out.println("After swap:  x=" + x + ", y=" + y);
    }
}
```

**How to run:** `java ToggleAdvanced.java`

`before ^ after` produces a mask where every bit that *differs* between the two snapshots is `1`, and every bit that is the *same* in both is `0` — this is exactly the "change detection" property that makes `^` useful for computing a minimal diff between two states without comparing them field by field. `printChangedFlags` then checks each named flag's bit against that diff mask, reporting only the flags that actually changed (and, using `before`'s own bit, which direction each one flipped). The XOR-swap trick is a direct, sequential application of the identities from Section 1: each line is a genuine XOR operation whose net effect (once you substitute and simplify algebraically) cancels out one of the two original values while preserving the other, ultimately exchanging `x` and `y` without ever needing a third temporary variable to hold one value while the other is overwritten.

## 6. Walkthrough

Trace the XOR-swap trick step by step with `x = 17, y = 42` (binary irrelevant to the logic, but conceptually: let `X` denote the original `17` and `Y` denote the original `42`):

**Line 1: `x = x ^ y`.** Before this line, `x = X = 17` and `y = Y = 42`. After it, `x` holds `X ^ Y`. `y` is untouched, still `Y = 42`.

**Line 2: `y = x ^ y`.** `x` currently holds `X ^ Y` (from line 1), and `y` still holds `Y`. So this computes `y = (X ^ Y) ^ Y`. Using the identity `a ^ b ^ b == a` (grouping the two `Y`s together, since XOR is associative and commutative), this simplifies to `y = X`. So after this line, `y` holds the *original* value of `x` (`17`), even though `x` itself was overwritten back in line 1.

**Line 3: `x = x ^ y`.** `x` currently holds `X ^ Y` (still, from line 1 — line 2 only changed `y`), and `y` now holds `X` (from line 2). So this computes `x = (X ^ Y) ^ X`. Regrouping the two `X`s together (`X ^ X ^ Y`), this simplifies to `x = Y`. So after this line, `x` holds the *original* value of `y` (`42`).

**Result.** `x` now holds `42` (the original `y`) and `y` now holds `17` (the original `x`) — a complete swap, achieved using only three XOR assignments and no third variable to temporarily hold either value.

```
Start:        x=17 (X),        y=42 (Y)
x = x^y:      x=X^Y,           y=Y           <- x now "encodes" both values combined
y = x^y:      x=X^Y,           y=(X^Y)^Y = X <- the Y cancels, y recovers the ORIGINAL x
x = x^y:      x=(X^Y)^X = Y,   y=X           <- the X cancels, x recovers the ORIGINAL y

Final:        x=42 (orig Y),  y=17 (orig X)   <- swapped!
```

**Practical caveat.** Despite being a classic educational demonstration of how `^`'s self-inverse property composes across multiple operations, this trick offers no real performance benefit on modern JVMs (a plain `int temp = x; x = y; y = temp;` is just as fast and dramatically more readable) and is generally considered an anti-pattern in production code for exactly that readability reason — it is included here because it is the clearest possible illustration of how `x ^ x == 0` and `x ^ 0 == x` interact.

## 7. Gotchas & takeaways

> **`^` (and its `boolean` form) has no short-circuit behavior at all — both operands always matter to the result.** Unlike `&&`/`||`, there is no "left side alone determines the answer" case for XOR, since flipping the right operand always flips the final result.

> **XOR-based "encoding" with a fixed key is trivially reversible and provides no real security** — anyone who discovers or guesses the key recovers the original data instantly. Use it only for lightweight obfuscation (deterring casual tampering), never as a substitute for real encryption.

- Bitwise `^` produces `1` in each bit position where the two operands differ, and `0` where they agree.
- `x ^ x == 0` and `x ^ 0 == x` for any `x` — these two identities make XOR its own inverse: applying the same XOR twice with the same operand restores the original value.
- `flags ^= BIT` is the idiomatic way to toggle a single bit (or a combination of bits, via a multi-bit mask) without needing to check its current state first.
- `before ^ after` computes a "diff mask" showing exactly which bits changed between two snapshots — useful for efficient state-change detection.
