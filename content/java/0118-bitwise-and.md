---
card: java
gi: 118
slug: bitwise-and
title: Bitwise AND &
---

## 1. What it is

`&` has two distinct meanings in Java depending on its operand types. On integer types (`int`, `long`, `short`, `byte`, `char`), `&` performs a **bitwise AND**: it compares each corresponding bit of the two operands and produces a `1` bit only where *both* operands have a `1` in that position. On `boolean` operands, `&` performs a **non-short-circuiting logical AND** — it computes the same `true`/`false` result as `&&`, but (unlike `&&`) it always evaluates both operands, even if the left one is already `false`.

```java
int a = 0b1100;   // 12
int b = 0b1010;   // 10
int result = a & b;   // 0b1000 = 8 — only bit position 3 has 1 in both
System.out.println(result);

boolean x = false;
boolean y = someExpensiveCheck();
boolean r = x & y;   // y IS evaluated even though x is already false (no short-circuit)
```

Because `&` on integers operates bit-by-bit independently, it is commonly used with a **mask** — a fixed pattern of bits — to extract or test specific bits out of a larger value, a technique that predates Java and comes directly from C-style bit manipulation.

## 2. Why & when

Bitwise `&` is the standard tool for:

- Extracting a subset of bits: `value & 0xFF` masks out everything except the low 8 bits.
- Testing whether a specific flag bit is set: `(permissions & WRITE_FLAG) != 0`.
- Fast parity/divisibility-by-power-of-2 checks: `n & 1` is `0` for even numbers, `1` for odd (equivalent to, but faster than, `n % 2`).
- Combined with `boolean` operands, `&` (not `&&`) is occasionally used deliberately when you *want* both sides evaluated regardless of the first result — for example, when both sides have necessary side effects that must always run, though this is rare and should be commented clearly since `&&` is almost always what's intended for plain conditionals.

## 3. Core concept

```java
public class BitwiseAndDemo {
    public static void main(String[] args) {
        // Basic bitwise AND
        int a = 0b1100;  // 12
        int b = 0b1010;  // 10
        System.out.println("a & b = " + (a & b) + " (binary: " + Integer.toBinaryString(a & b) + ")");  // 8, "1000"

        // Masking: extract the low byte of a larger number
        int value = 0x1234ABCD;
        int lowByte = value & 0xFF;
        System.out.printf("Low byte of 0x%08X: 0x%02X%n", value, lowByte);   // 0xCD

        // Flag testing
        int READ = 0b001, WRITE = 0b010, EXEC = 0b100;
        int permissions = READ | EXEC;   // has read and execute, not write
        System.out.println("Has WRITE? " + ((permissions & WRITE) != 0));   // false
        System.out.println("Has READ?  " + ((permissions & READ) != 0));    // true

        // Even/odd check via bitwise AND
        int n = 17;
        System.out.println(n + " is " + ((n & 1) == 0 ? "even" : "odd"));

        // Non-short-circuiting boolean &: both sides always evaluate, unlike &&
        boolean left = false;
        boolean right = logAndReturn(true);   // this call happens even though `left` is already false
        System.out.println("left & right = " + (left & right));
    }

    static boolean logAndReturn(boolean value) {
        System.out.println("  right operand evaluated");
        return value;
    }
}
```

## 4. Diagram

<svg viewBox="0 0 700 155" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Bitwise AND diagram: 12 in binary 1100 AND 10 in binary 1010, computed bit by bit, gives 1000 which is 8. Only the bit position where both operands have a 1 survives.">
  <rect x="8" y="8" width="684" height="139" rx="8" fill="#0d1117"/>
  <text x="350" y="24" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">0b1100 (12) &amp; 0b1010 (10) — bit by bit, right to left</text>

  <text x="200" y="52" fill="#e6edf3" font-size="14" text-anchor="middle" font-family="monospace">1  1  0  0</text>
  <text x="200" y="74" fill="#e6edf3" font-size="14" text-anchor="middle" font-family="monospace">1  0  1  0</text>
  <line x1="130" y1="82" x2="270" y2="82" stroke="#8b949e" stroke-width="1.5"/>
  <text x="200" y="100" fill="#6db33f" font-size="14" text-anchor="middle" font-family="monospace">1  0  0  0</text>
  <text x="200" y="122" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">= 8 (only the bit where BOTH inputs are 1 survives)</text>

  <text x="500" y="52" fill="#8b949e" font-size="9" font-family="monospace">bit 3: 1 &amp; 1 = 1</text>
  <text x="500" y="70" fill="#8b949e" font-size="9" font-family="monospace">bit 2: 1 &amp; 0 = 0</text>
  <text x="500" y="88" fill="#8b949e" font-size="9" font-family="monospace">bit 1: 0 &amp; 1 = 0</text>
  <text x="500" y="106" fill="#8b949e" font-size="9" font-family="monospace">bit 0: 0 &amp; 0 = 0</text>
</svg>

`&` computes each output bit independently — a `1` survives only where both inputs had a `1` in that exact position.

## 5. Runnable example

Scenario: a file-permission checker (like a simplified Unix `chmod` system) that stores read/write/execute flags in a single `int` bitmask — extended to extract individual permission bits and check multiple flags at once.

### Level 1 — Basic

```java
public class PermissionsBasic {
    static final int READ = 0b100, WRITE = 0b010, EXECUTE = 0b001;

    public static void main(String[] args) {
        int filePermissions = READ | WRITE;   // this file is readable and writable, not executable

        boolean canRead = (filePermissions & READ) != 0;
        boolean canWrite = (filePermissions & WRITE) != 0;
        boolean canExecute = (filePermissions & EXECUTE) != 0;

        System.out.println("Permissions: " + Integer.toBinaryString(filePermissions));
        System.out.println("Can read:    " + canRead);      // true
        System.out.println("Can write:   " + canWrite);      // true
        System.out.println("Can execute: " + canExecute);     // false
    }
}
```

**How to run:** `java PermissionsBasic.java`

`filePermissions & READ` isolates just the `READ` bit position: since `filePermissions` is `0b110` and `READ` is `0b100`, the AND result is `0b100`, which is non-zero, so `canRead` is `true`. `filePermissions & EXECUTE` computes `0b110 & 0b001 = 0b000`, which is zero, so `canExecute` is `false` — this "mask, then check non-zero" pattern is the standard idiom for testing individual flag bits within a combined bitmask.

### Level 2 — Intermediate

Same permission system, now checking for *combinations* of required permissions at once, and extracting a permission subset using a compound mask built from multiple flags.

```java
public class PermissionsIntermediate {
    static final int READ = 0b100, WRITE = 0b010, EXECUTE = 0b001;

    static boolean hasAll(int permissions, int required) {
        // ALL bits in `required` must be present in `permissions`
        return (permissions & required) == required;
    }

    static boolean hasAny(int permissions, int flags) {
        // AT LEAST ONE bit in `flags` must be present in `permissions`
        return (permissions & flags) != 0;
    }

    public static void main(String[] args) {
        int filePermissions = READ | WRITE;

        System.out.println("Has READ+WRITE:        " + hasAll(filePermissions, READ | WRITE));   // true
        System.out.println("Has READ+WRITE+EXECUTE: " + hasAll(filePermissions, READ | WRITE | EXECUTE)); // false
        System.out.println("Has any of WRITE/EXEC:  " + hasAny(filePermissions, WRITE | EXECUTE));  // true (has WRITE)
        System.out.println("Has any of EXEC only:    " + hasAny(filePermissions, EXECUTE));           // false
    }
}
```

**How to run:** `java PermissionsIntermediate.java`

`hasAll` checks that masking `permissions` with `required` gives back *exactly* `required` — this is only true if every bit set in `required` was also set in `permissions` (if any required bit were missing, that bit would come out as `0` in the AND result, making the result unequal to `required`). `hasAll(filePermissions, READ | WRITE | EXECUTE)` fails because `EXECUTE`'s bit is missing from `filePermissions`, so the AND result (`0b110`) doesn't equal the full required mask (`0b111`). `hasAny` uses the simpler "non-zero" check from Level 1, but against a combined mask of multiple flags, testing whether *any* of them overlap with `permissions`.

### Level 3 — Advanced

Same permission system, now extended to a full Unix-style `rwxrwxrwx` (owner/group/other) permission model packed into a 9-bit mask, extracting each group's 3-bit sub-permission using a shift-and-mask combination, and building a human-readable string representation — the real-world technique behind tools like `ls -l`.

```java
public class PermissionsAdvanced {
    static final int R = 0b100, W = 0b010, X = 0b001;

    // Bit layout (9 bits total): [owner: bits 8-6][group: bits 5-3][other: bits 2-0]
    static int buildMode(int owner, int group, int other) {
        return (owner << 6) | (group << 3) | other;
    }

    static String describeGroup(int mode, int shift) {
        int group = (mode >> shift) & 0b111;   // shift the target group down, then mask to isolate 3 bits
        StringBuilder sb = new StringBuilder();
        sb.append((group & R) != 0 ? 'r' : '-');
        sb.append((group & W) != 0 ? 'w' : '-');
        sb.append((group & X) != 0 ? 'x' : '-');
        return sb.toString();
    }

    static String describeMode(int mode) {
        return describeGroup(mode, 6)   // owner
             + describeGroup(mode, 3)    // group
             + describeGroup(mode, 0);    // other
    }

    public static void main(String[] args) {
        int mode644 = buildMode(R | W, R, R);          // typical file: rw-r--r--
        int mode755 = buildMode(R | W | X, R | X, R | X); // typical executable: rwxr-xr-x

        System.out.printf("Mode 0644: %09s -> %s%n", Integer.toBinaryString(mode644), describeMode(mode644));
        System.out.printf("Mode 0755: %09s -> %s%n", Integer.toBinaryString(mode755), describeMode(mode755));
    }
}
```

**How to run:** `java PermissionsAdvanced.java`

`describeGroup(mode, shift)` first right-shifts `mode` by `shift` bits (`>>`, covered separately), moving the target 3-bit group down to the lowest positions, then applies `& 0b111` to mask off everything except those 3 bits — this "shift right, then AND-mask" combination is the standard technique for extracting an arbitrary sub-field from a packed bitmask, used throughout systems programming (file permissions, network protocol headers, hardware registers). For `mode755` (binary `111101101`), extracting the "group" field (`shift = 3`) computes `mode755 >> 3 = 0b111101` then `& 0b111 = 0b101`, correctly isolating the middle three bits (`r-x` for the group).

## 6. Walkthrough

Trace `describeGroup(mode755, 3)` where `mode755 = buildMode(0b111, 0b101, 0b101) = 0b111_101_101` (`0o755` in octal, the familiar Unix mode number):

**Build the mode.** `buildMode(7, 5, 5)` computes `(7 << 6) | (5 << 3) | 5`. `7 << 6` shifts `0b111` left by 6, giving `0b111000000`. `5 << 3` shifts `0b101` left by 3, giving `0b000101000`. OR-ing all three together (`0b111000000 | 0b000101000 | 0b000000101`) gives `0b111101101`.

**Shift for the group field.** `describeGroup(mode755, 3)` computes `mode755 >> 3`. Shifting `0b111101101` right by 3 positions drops the lowest 3 bits (`101`, the "other" field) and gives `0b111101`.

**Mask to isolate 3 bits.** `0b111101 & 0b111` keeps only the lowest 3 bits of the shifted value: `0b101`. Bits above position 2 are masked to `0` by the `& 0b111`, discarding the "owner" field's contribution that's still present higher up in the shifted value.

**Build the string.** `group = 0b101`. `(group & R) != 0` checks `0b101 & 0b100 = 0b100`, non-zero, so `'r'` is appended. `(group & W) != 0` checks `0b101 & 0b010 = 0b000`, zero, so `'-'` is appended. `(group & X) != 0` checks `0b101 & 0b001 = 0b001`, non-zero, so `'x'` is appended. The result is `"r-x"`.

```
mode755 = 111 101 101   (owner=111, group=101, other=101)

describeGroup(mode755, shift=3):
  mode755 >> 3  = 000 111 101      (drops "other" bits off the right)
  & 0b111       =         101      (masks away everything above bit 2 -- discards "owner" bits)
  group = 101  ->  r=1,w=0,x=1  ->  "r-x"
```

**Final output.** `describeMode` calls `describeGroup` three times with shifts `6`, `3`, and `0`, concatenating `"rwx"` (owner), `"r-x"` (group), and `"r-x"` (other) into the familiar `"rwxr-xr-x"` string, matching the conventional Unix `755` executable permission display.

## 7. Gotchas & takeaways

> **`&` on `boolean` operands does not short-circuit — both sides are always evaluated.** Using `&` where `&&` was intended (perhaps by typo) silently removes the short-circuit protection, potentially causing a `NullPointerException` or unwanted side effect that `&&` would have prevented.

> **`(value & mask) != 0` tests "any bit in the mask is set"; `(value & mask) == mask` tests "all bits in the mask are set."** These two checks are easy to confuse — using the wrong one silently changes "has at least one permission" into "has every permission" or vice versa.

- Bitwise `&` on integers produces `1` in each bit position only where both operands have `1` there — the standard tool for masking and flag-testing.
- `value & mask` extracts/tests bits; `(value >> shift) & mask` extracts an arbitrary sub-field from a packed multi-field value.
- Boolean `&` computes the same result as `&&` but always evaluates both operands — prefer `&&` for ordinary conditionals unless you specifically need both sides evaluated regardless.
- `n & 1` is a fast, idiomatic even/odd check, equivalent to `n % 2 == 0` for the "even" case.
