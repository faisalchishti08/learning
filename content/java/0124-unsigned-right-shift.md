---
card: java
gi: 124
slug: unsigned-right-shift
title: Unsigned right shift >>>
---

## 1. What it is

`>>>` shifts the bits of its left operand toward the lower-order (right) end, exactly like `>>`, but it always fills the vacated high-order bits with `0`, regardless of the operand's sign. This makes it a **logical** (as opposed to arithmetic) shift: it treats the operand's bit pattern purely as a sequence of bits, ignoring what those bits mean as a signed number. For non-negative operands, `>>>` and `>>` produce identical results, since the sign bit is already `0` and both operators fill with `0`. The difference only appears for negative operands.

```java
int positive = 16;
System.out.println(positive >>> 2);   // 4 — same as >> for non-negative values

int negative = -16;
System.out.println(negative >> 2);      // -4  (signed: fills with 1s, preserves sign)
System.out.println(negative >>> 2);      // 1073741820 (unsigned: fills with 0s, huge positive result)
```

`>>>` exists specifically because Java has no unsigned integer *types* (unlike some languages, or unlike Java's own unsigned-focused static methods added later) — `>>>` is the one operator that lets you treat a signed `int`/`long`'s bit pattern as if it were unsigned, at least for the purpose of shifting.

## 2. Why & when

`>>>` is used specifically when a value's bits represent something that is not conceptually a signed number, but the variable's declared type is still a signed `int`/`long`:

- Working with hash codes: many hashing algorithms mix a hash's bits using `hash >>> 16` (rather than `>>`) specifically to avoid sign-extension artifacts, since a hash code's "value" as a number is meaningless — only its bit pattern matters.
- Bit-scanning/counting algorithms that need to examine raw bits without the sign bit "contaminating" the shifted-in positions.
- Emulating genuinely unsigned arithmetic in a limited way: shifting a value that represents an unsigned quantity (like a raw 32-bit color, checksum, or hardware register) without accidentally sign-extending it.

You would *not* use `>>>` for ordinary signed arithmetic like fixed-point division, where preserving the sign (via `>>`) is exactly what you want.

## 3. Core concept

```java
public class UnsignedRightShiftDemo {
    public static void main(String[] args) {
        // For non-negative values, >> and >>> agree
        int positive = 16;
        System.out.println("16 >> 2  = " + (positive >> 2));    // 4
        System.out.println("16 >>> 2 = " + (positive >>> 2));     // 4 — same

        // For negative values, they diverge sharply
        int negative = -16;
        System.out.println("-16 >> 2  = " + (negative >> 2));      // -4 (sign preserved)
        System.out.println("-16 >>> 2 = " + (negative >>> 2));       // huge positive number (sign bit zero-filled)

        // >>> is the standard way to view a negative int's "raw bit pattern" as unsigned
        int allOnes = -1;    // in binary: 32 ones
        System.out.println("-1 >>> 28 = " + (allOnes >>> 28));    // 15 (the low 4 bits, all originally 1s, shifted down)

        // Practical use: a hash-mixing step common in real hash functions
        int hash = 0x9E3779B9;   // an arbitrary example hash value
        int mixed = hash ^ (hash >>> 16);
        System.out.printf("Mixed hash: 0x%08X%n", mixed);
    }
}
```

## 4. Diagram

<svg viewBox="0 0 700 175" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Signed versus unsigned right shift diagram: negative 16 shifted signed right by 2 fills vacated high bits with 1, preserving the negative sign and giving negative 4. The same value shifted unsigned right by 2 fills vacated high bits with 0, giving a large positive number instead.">
  <rect x="8" y="8" width="684" height="159" rx="8" fill="#0d1117"/>
  <text x="350" y="24" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">-16 &gt;&gt; 2 vs. -16 &gt;&gt;&gt; 2 — same bits shifted, different fill value</text>

  <rect x="16" y="34" width="330" height="118" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="181" y="52" fill="#6db33f" font-size="8.5" text-anchor="middle" font-family="sans-serif">Signed &gt;&gt; (arithmetic)</text>
  <text x="30" y="74" fill="#e6edf3" font-size="9" font-family="monospace">1111...110000 &gt;&gt; 2</text>
  <text x="30" y="94" fill="#79c0ff" font-size="9" font-family="monospace">fills with 1s (sign bit)</text>
  <text x="30" y="114" fill="#79c0ff" font-size="9" font-family="monospace">1111...111100</text>
  <text x="30" y="134" fill="#6db33f" font-size="9" font-family="monospace">= -4 (sign preserved)</text>

  <rect x="356" y="34" width="328" height="118" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="520" y="52" fill="#79c0ff" font-size="8.5" text-anchor="middle" font-family="sans-serif">Unsigned &gt;&gt;&gt; (logical)</text>
  <text x="370" y="74" fill="#e6edf3" font-size="9" font-family="monospace">1111...110000 &gt;&gt;&gt; 2</text>
  <text x="370" y="94" fill="#79c0ff" font-size="9" font-family="monospace">fills with 0s (always)</text>
  <text x="370" y="114" fill="#79c0ff" font-size="9" font-family="monospace">0011...111100</text>
  <text x="370" y="134" fill="#79c0ff" font-size="9" font-family="monospace">= 1073741820 (huge positive)</text>
</svg>

The identical starting bit pattern produces wildly different results depending on whether the shift is signed (`>>`, sign-preserving) or unsigned (`>>>`, always zero-filling).

## 5. Runnable example

Scenario: implementing a simple, well-known hash-mixing function (similar in spirit to techniques used in `HashMap`'s internals and other hashing algorithms) that spreads a hash code's high bits into its low bits — a genuine, real-world use of `>>>` — extended to safely comparing and printing raw 32-bit values as unsigned.

### Level 1 — Basic

```java
public class HashMixBasic {
    public static void main(String[] args) {
        int hash = "example".hashCode();

        // A common hash-spreading technique: XOR the hash with its own upper bits shifted down
        int spread = hash ^ (hash >>> 16);

        System.out.println("Original hash: " + hash);
        System.out.println("Spread hash:   " + spread);
    }
}
```

**How to run:** `java HashMixBasic.java`

`hash >>> 16` shifts the top 16 bits of the hash down into the low 16 bit positions, filling the vacated top 16 bits with `0` — using `>>>` here (rather than `>>`) is deliberate: a hash code's bit pattern is not meant to be interpreted as a signed number at all, so sign-extending it with `>>` would be conceptually wrong, even though it would still compile and run without error. XOR-ing the shifted value back into the original hash mixes the high-order bits' entropy into the low-order bits, which helps distribute hash values more evenly across a hash table's buckets (since many hash table implementations only use a value's low bits to select a bucket).

### Level 2 — Intermediate

Same hash-mixing utility, now demonstrating why `>>` would be a subtle bug here for negative hash codes, and printing a raw 32-bit value as its true unsigned decimal representation using `Integer.toUnsignedLong` alongside `>>>`.

```java
public class HashMixIntermediate {

    static int spreadHashCorrect(int hash) {
        return hash ^ (hash >>> 16);   // correct: treats hash bits as unsigned data
    }

    static int spreadHashBuggy(int hash) {
        return hash ^ (hash >> 16);     // bug: sign-extends, mixing in artificial 1-bits for negative hashes
    }

    public static void main(String[] args) {
        int negativeHash = -123456789;   // a hash code that happens to be negative — common and normal in Java

        int correct = spreadHashCorrect(negativeHash);
        int buggy = spreadHashBuggy(negativeHash);

        System.out.println("Correct (>>> ) spread: " + correct);
        System.out.println("Buggy   (>>  ) spread: " + buggy);
        System.out.println("Do they differ? " + (correct != buggy));   // true — genuinely different results

        // Viewing a negative int's true unsigned magnitude
        int rawValue = -1;
        System.out.println("-1 as signed:    " + rawValue);
        System.out.println("-1 as unsigned:  " + Integer.toUnsignedLong(rawValue));   // 4294967295
        System.out.println("-1 >>> 16:        " + (rawValue >>> 16));                   // 65535, a meaningful "raw bits" view
    }
}
```

**How to run:** `java HashMixIntermediate.java`

For a negative `hash`, `hash >> 16` (the buggy version) sign-extends: the vacated top 16 bits fill with `1`s instead of `0`s, because `>>` interprets the negative hash as a "real" signed number whose sign must be preserved. This means `hash >> 16` produces a value with its top 16 bits all `1`s, and XOR-ing that back into `hash` mixes in a very different (and less useful, for hashing purposes) pattern than the correct `>>>` version does — the two spread functions produce genuinely different results for negative inputs, confirmed by the `correct != buggy` check. `Integer.toUnsignedLong(-1)` shows the "true" unsigned magnitude of `-1`'s bit pattern (`4294967295`, i.e., `2^32 - 1`) — this is the value `>>>` conceptually treats the bit pattern as representing, even though the variable's static type remains a signed `int`.

### Level 3 — Advanced

A genuinely practical use combining `>>>` with bit-counting: implementing a simple "count leading zeros" style utility by hand (Java's actual `Integer.numberOfLeadingZeros` exists and should be preferred in real code, but building an equivalent by hand demonstrates exactly why `>>>` — not `>>` — is required for a correct, general-purpose bit-scanning loop).

```java
public class HashMixAdvanced {

    static int countLeadingZerosManual(int value) {
        if (value == 0) return 32;
        int count = 0;
        int remaining = value;
        // Repeatedly check the highest bit by comparing against 0 after an unsigned shift.
        // Using >>> ensures negative inputs are treated as raw bit patterns, not sign-extended.
        while ((remaining >>> 31) == 0) {   // is the current highest bit 0?
            count++;
            remaining = remaining << 1;      // shift left to bring the next bit into position 31
        }
        return count;
    }

    public static void main(String[] args) {
        System.out.println("countLeadingZeros(1):          " + countLeadingZerosManual(1));           // 31
        System.out.println("countLeadingZeros(256):        " + countLeadingZerosManual(256));          // 23
        System.out.println("countLeadingZeros(-1):         " + countLeadingZerosManual(-1));             // 0 (sign bit already 1)
        System.out.println("countLeadingZeros(0):          " + countLeadingZerosManual(0));               // 32

        // Cross-check against the JDK's own built-in implementation
        System.out.println("JDK Integer.numberOfLeadingZeros(256): " + Integer.numberOfLeadingZeros(256));
    }
}
```

**How to run:** `java HashMixAdvanced.java`

`remaining >>> 31` shifts the entire 32-bit value right by 31 positions, leaving only the original highest bit (bit 31) in position 0, with `0`s filled in above it — critically, using `>>>` here means this works correctly regardless of whether `remaining` is currently negative (has its own bit 31 set to `1`) or positive; a signed `>>` would still technically produce the correct single-bit check for this specific `>> 31` case (since sign-extension by exactly 31 positions coincidentally reproduces the original bit 31 in position 0 either way), but using `>>>` throughout signals the *intent* clearly — that this code deliberately treats the `int` as a raw 32-bit pattern, not a signed number — which becomes essential the moment the shift amount is anything other than exactly `31`. The loop counts how many leading `0` bits appear before the first `1` bit, terminating as soon as `remaining >>> 31` is non-zero (meaning the highest bit is now `1`).

## 6. Walkthrough

Trace `countLeadingZerosManual(256)` where `256` in binary is `00000000 00000000 00000001 00000000` (bit 8 set):

**Initial check.** `remaining = 256`. `remaining >>> 31` shifts all 32 bits right by 31, leaving only the original bit 31 (which is `0`, since `256` is far smaller than `Integer.MAX_VALUE`) in position 0: the result is `0`. Since this equals `0`, the loop body executes.

**Iterations 1 through 23.** Each iteration increments `count` and shifts `remaining` left by 1, moving the single set bit (originally at position 8) one position higher each time. After 23 iterations, the set bit has moved from position 8 up to position 31 (`8 + 23 = 31`), and `remaining` is now `10000000 00000000 00000000 00000000` (a negative `int`, since bit 31 — the sign bit — is now `1`).

**Loop check after iteration 23.** `remaining >>> 31` now shifts this value right by 31, leaving just the (now-set) bit 31 in position 0: the result is `1`, not `0`. The `while` condition `(remaining >>> 31) == 0` is now `false`, so the loop exits.

**Result.** `count` holds `23`, correctly reporting that `256`'s binary representation (`00000000 00000000 00000001 00000000`) has 23 leading zero bits before its first `1` bit (at position 8, counting from 0).

```
remaining = 256 = 00000000 00000000 00000001 00000000
                                              ^ bit 8

Loop shifts left each iteration, moving the 1-bit up by one position per step:
  after 23 shifts: 10000000 00000000 00000000 00000000
                    ^ bit 31 (now the sign bit)

remaining >>> 31 == 1 now (not 0)  -> loop stops, count = 23
```

**Why `>>>` (not `>>`) matters for the general check.** Once `remaining` becomes negative partway through the loop (as it does here, once the set bit reaches position 31), a plain `>> 31` would still happen to give the same single-bit answer for this exact shift amount, purely because sign-extending by the full 31 positions reproduces bit 31 in position 0 regardless of fill method — but this is a coincidence specific to shifting by exactly one less than the bit width. Any bit-scanning code that needs a genuinely unsigned comparison at an arbitrary shift amount (not just 31) requires `>>>` to behave correctly for all cases, which is why it is the conventionally correct and clearly-intentioned choice here.

## 7. Gotchas & takeaways

> **`>>>` always fills vacated high bits with `0`, regardless of sign — this is the defining difference from `>>`, which fills with copies of the sign bit.** For non-negative operands the two are identical; they diverge only for negative operands, where `>>>` produces a large positive result instead of preserving the negative sign.

> **Use `>>>` when a value's bit pattern is not conceptually a signed number** — hash codes, raw bitmasks, checksums, hardware register values — **and `>>` when it genuinely is** a signed quantity you want to preserve the sign of (like fixed-point arithmetic or a signed sub-field extraction).

- `>>>` is a logical (zero-filling) right shift; `>>` is an arithmetic (sign-preserving) right shift. They agree for non-negative operands and diverge for negative ones.
- `Integer.toUnsignedLong`/`Long.toUnsignedString` let you view a value's "true" unsigned magnitude, which is conceptually what `>>>` operates on.
- Hash-mixing functions conventionally use `>>>` (not `>>`) specifically because a hash's bit pattern isn't meant to be interpreted as a signed number.
- Java's built-in `Integer.numberOfLeadingZeros`, `Integer.bitCount`, and similar utility methods already implement common bit-scanning operations correctly and efficiently — prefer them over hand-rolled loops in real code; the manual version here is purely for understanding why `>>>` matters.
