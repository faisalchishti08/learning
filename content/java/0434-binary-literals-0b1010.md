---
card: java
gi: 434
slug: binary-literals-0b1010
title: Binary literals (0b1010)
---

## 1. What it is

Java 7 added binary integer literals: writing `0b` (or `0B`) followed by a sequence of `0`s and `1`s produces an `int` (or, with an `L` suffix, a `long`) whose value is exactly that binary number — `0b1010` is the same value as `10` in decimal or `0xA` in hexadecimal, just written in a base that directly shows which bits are set.

## 2. Why & when

Whenever code is fundamentally about **individual bits** — permission flags, hardware register states, protocol byte layouts — decimal or even hexadecimal literals hide the very thing you're trying to reason about: which specific bits are `1` and which are `0`. Before binary literals, expressing "bits 1 and 3 are set" meant writing `10` (decimal) or `0xA` (hex) and mentally converting to binary to verify it was correct. `0b1010` states the bit pattern directly — no conversion required, and the literal itself documents exactly what it represents.

You reach for binary literals any time the *bit pattern* is the meaningful piece of information: defining bitmask constants for flags, modeling a hardware status register, or working with binary protocols where specific bit positions carry specific meaning.

## 3. Core concept

```java
int flags = 0b1010;         // decimal 10 -- bits 1 and 3 are set (counting from bit 0)
long bigMask = 0b1111_0000L; // 'L' suffix for long; underscore groups digits for readability (see next tutorial)

System.out.println(flags);                          // 10 (still just an int -- prints in decimal by default)
System.out.println(Integer.toBinaryString(flags));   // "1010" -- convert back to a binary STRING to display it
```

Binary literals are purely a *source-code* convenience — once compiled, `0b1010` and `10` are indistinguishable `int` values. The binary form only exists to make bit patterns readable at the point where you write them.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="0b1010, 10 decimal, and 0xA hexadecimal all represent the exact same int value; the binary form is the only one that shows the individual bit pattern directly in the source code">
  <rect x="8" y="8" width="624" height="134" rx="8" fill="#0d1117"/>
  <text x="20" y="26" fill="#e6edf3" font-size="11" font-family="sans-serif">All three of these are the SAME int value, 10:</text>
  <rect x="30" y="40" width="150" height="30" rx="4" fill="#1c2430" stroke="#6db33f"/><text x="105" y="60" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">0b1010 (binary)</text>
  <rect x="200" y="40" width="150" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="275" y="60" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">10 (decimal)</text>
  <rect x="370" y="40" width="150" height="30" rx="4" fill="#1c2430" stroke="#e6edf3"/><text x="445" y="60" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">0xA (hexadecimal)</text>
  <text x="320" y="100" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Only the binary form shows "bit 1 and bit 3 are set" directly, with no mental conversion needed.</text>
</svg>

Same value, three notations — binary literals are chosen specifically when the bit pattern itself is the meaningful part.

## 5. Runnable example

Scenario: a permission-flags system, then a simulated CPU status register — the same bitmask technique, evolved from a single binary literal, through combining named flag constants with bitwise operators, to reading and modifying individual bits of a simulated hardware register.

### Level 1 — Basic

```java
public class PermissionsBasic {
    public static void main(String[] args) {
        int flags = 0b1010; // binary literal: bit 1 and bit 3 set
        System.out.println("flags = " + flags + " (binary: " + Integer.toBinaryString(flags) + ")");
    }
}
```

**How to run:** `java PermissionsBasic.java`

`0b1010` is written to directly show which bits are set (bit 1 and bit 3, counting from bit 0), but it's still just the `int` value `10` — `Integer.toBinaryString` converts it back to a binary-formatted `String` purely for display.

### Level 2 — Intermediate

```java
public class PermissionsFlags {
    static final int READ    = 0b001;
    static final int WRITE   = 0b010;
    static final int EXECUTE = 0b100;

    public static void main(String[] args) {
        int userPerms = READ | WRITE; // combine flags with bitwise OR
        System.out.println("User perms: " + Integer.toBinaryString(userPerms));

        System.out.println("Can read? " + ((userPerms & READ) != 0));
        System.out.println("Can write? " + ((userPerms & WRITE) != 0));
        System.out.println("Can execute? " + ((userPerms & EXECUTE) != 0));
    }
}
```

**How to run:** `java PermissionsFlags.java`

Each named constant (`READ`, `WRITE`, `EXECUTE`) occupies its own distinct bit, written in binary specifically so the "one bit per flag" design is visible at a glance. `|` combines flags into one value; `&` followed by `!= 0` checks whether a specific flag's bit is set within that combined value.

### Level 3 — Advanced

```java
public class StatusRegister {
    // A simulated 8-bit CPU status register, using binary literals for direct bit-position readability
    static final int FLAG_ZERO      = 0b0000_0001;
    static final int FLAG_CARRY     = 0b0000_0010;
    static final int FLAG_OVERFLOW  = 0b0000_0100;
    static final int FLAG_NEGATIVE  = 0b0000_1000;

    static void printFlags(int register) {
        System.out.printf("Register: %8s  Zero=%b Carry=%b Overflow=%b Negative=%b%n",
            String.format("%8s", Integer.toBinaryString(register)).replace(' ', '0'),
            (register & FLAG_ZERO) != 0,
            (register & FLAG_CARRY) != 0,
            (register & FLAG_OVERFLOW) != 0,
            (register & FLAG_NEGATIVE) != 0);
    }

    public static void main(String[] args) {
        int register = 0b0000_0000;
        printFlags(register);

        register |= FLAG_CARRY;      // an operation sets the carry flag
        printFlags(register);

        register |= FLAG_NEGATIVE;   // and now also the negative flag
        printFlags(register);

        register &= ~FLAG_CARRY;     // clear just the carry flag
        printFlags(register);
    }
}
```

**How to run:** `java StatusRegister.java`

The underscores inside `0b0000_0001` (grouping into nibbles) make an 8-bit pattern much easier to read than one unbroken run of eight digits — a preview of the very next tutorial's feature. `|=` sets a specific bit without disturbing the others; `&= ~FLAG_CARRY` clears just that one bit by ANDing with its bitwise complement, a standard bit-manipulation idiom.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `register` starts at `0b0000_0000` (all flags clear, value `0`). `printFlags(0)` prints all four flags as `false`, with the binary display `00000000`.

`register |= FLAG_CARRY` is shorthand for `register = register | FLAG_CARRY`. Since `FLAG_CARRY` is `0b0000_0010` (bit 1), ORing it into `register` (currently all zeros) sets exactly that bit, making `register` become `0b0000_0010` (decimal `2`). `printFlags(2)` shows `Carry=true`, all others still `false`.

`register |= FLAG_NEGATIVE` similarly sets bit 3 (`0b0000_1000`) without disturbing the already-set carry bit, since OR only ever turns bits *on*, never off — `register` becomes `0b0000_1010` (decimal `10`). `printFlags(10)` shows both `Carry=true` and `Negative=true`.

`register &= ~FLAG_CARRY` is shorthand for `register = register & (~FLAG_CARRY)`. `~FLAG_CARRY` flips every bit of `0b0000_0010`, producing a value with a `0` specifically at bit 1 and `1`s everywhere else. ANDing `register` (`0b0000_1010`) with this complement clears bit 1 (forcing it to `0`) while leaving every other bit exactly as it was — the result is `0b0000_1000` (decimal `8`), with the negative flag still set but carry now cleared. `printFlags(8)` confirms `Carry=false`, `Negative=true`.

Expected output:
```
Register: 00000000  Zero=false Carry=false Overflow=false Negative=false
Register: 00000010  Zero=false Carry=true Overflow=false Negative=false
Register: 00001010  Zero=false Carry=true Overflow=false Negative=true
Register: 00001000  Zero=false Carry=false Overflow=false Negative=true
```

## 7. Gotchas & takeaways

> Binary literals are purely notational — the compiler produces the exact same `int`/`long` value as an equivalent decimal or hexadecimal literal would. Don't expect any runtime distinction or special type; `0b1010 == 10` is `true`, and `Integer.toBinaryString` (or similar) is always needed if you actually want to *display* a value in binary form afterward.

- `0b`/`0B` prefixes a binary integer literal; without an `L` suffix it's an `int`, with `L` it's a `long`.
- Binary literals exist purely to make bit patterns readable in source code — they carry no runtime distinction from decimal or hex literals of the same value.
- Use `|` to set bits (combine flags), `&` paired with `!= 0` to test whether a specific bit is set, and `&= ~flag` to clear one specific bit without affecting others.
- Naming each flag as a `static final int` with a single bit set (one flag per bit position) is the standard bitmask pattern, and binary literals make that "one bit each" intent visually obvious.
- `Integer.toBinaryString(value)` (and the `Long` equivalent) is the standard way to display a value's binary representation at runtime — the literal notation only controls how you *write* a value in source, not how it's *printed*.
