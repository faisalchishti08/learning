---
card: java
gi: 121
slug: bitwise-complement
title: Bitwise complement ~
---

## 1. What it is

`~` is a unary operator that flips every bit of its integer operand: every `0` becomes `1`, and every `1` becomes `0`. Like other integer operators, it applies unary numeric promotion first (`byte`/`short`/`char` widen to `int`), so the result is always at least an `int`. Because Java integers use two's-complement representation, `~x` is mathematically equivalent to `-x - 1` (or, equivalently, `-(x + 1)`) — flipping every bit of a number always lands on this specific value.

```java
int x = 5;              // 0000...0101
int notX = ~x;           // 1111...1010 = -6
System.out.println(notX);  // -6

System.out.println(~0);     // -1  (all bits become 1, which is -1 in two's complement)
System.out.println(~-1);     // 0   (all bits of -1 are already 1; flipping gives all 0)
```

`~` is most useful not for its arithmetic identity but for building an **inverse mask**: `~SOME_BIT` produces a value with every bit set to `1` except the one(s) in `SOME_BIT`, which is exactly the pattern needed to "clear a bit" using `&`.

## 2. Why & when

`~` shows up almost exclusively in bit-manipulation code:

- Clearing a specific bit or set of bits: `flags &= ~BIT;` — ANDing with the complement of `BIT` forces that bit to `0` while leaving every other bit untouched.
- Building a mask that excludes certain bits: `~0xFF` gives a mask with every bit set except the low 8, useful for clearing a byte-sized field within a larger value.
- Occasionally seen in low-level algorithms (hashing, checksums) that exploit the two's-complement identity `~x == -x - 1` directly, though this is rarer in typical application code.

The most common mistake with `~` is forgetting that it produces the complement across the *entire* width of the type (32 bits for `int`, 64 for `long`) — `~0b0101` is not `0b1010`, it is a 32-bit value with every one of its upper 28 bits also flipped to `1`, which as a signed `int` prints as a large negative number, not the small 4-bit pattern a beginner might expect.

## 3. Core concept

```java
public class BitwiseComplementDemo {
    public static void main(String[] args) {
        int x = 5;
        System.out.println("x    = " + Integer.toBinaryString(x));         // "101"
        System.out.println("~x   = " + Integer.toBinaryString(~x));         // all upper bits flipped too
        System.out.println("~x as int = " + ~x);                            // -6

        // The two's-complement identity: ~x == -x - 1
        System.out.println("-x - 1 = " + (-x - 1));   // -6, matches ~x

        // Complement of 0 and -1
        System.out.println("~0  = " + ~0);    // -1
        System.out.println("~-1 = " + ~(-1)); // 0

        // Building an inverse mask to clear specific bits
        int flags = 0b1111;
        int BIT_TO_CLEAR = 0b0010;
        int mask = ~BIT_TO_CLEAR;     // all bits set except bit 1
        int cleared = flags & mask;    // clears exactly bit 1, leaves the rest
        System.out.println("flags:   " + Integer.toBinaryString(flags));
        System.out.println("cleared: " + Integer.toBinaryString(cleared));   // "1101"
    }
}
```

## 4. Diagram

<svg viewBox="0 0 700 165" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Bitwise complement diagram: complement of 5, which is 32 bits of zero followed by 101, flips every single bit, including all the leading zeros, producing a value with 28 leading ones, which as a signed int is negative 6.">
  <rect x="8" y="8" width="684" height="149" rx="8" fill="#0d1117"/>
  <text x="350" y="24" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">~5 flips ALL 32 bits, not just the visible low bits</text>

  <text x="20" y="52" fill="#e6edf3" font-size="9" font-family="monospace">int x = 5:</text>
  <text x="20" y="70" fill="#8b949e" font-size="10" font-family="monospace">00000000 00000000 00000000 00000101</text>

  <text x="20" y="98" fill="#e6edf3" font-size="9" font-family="monospace">~x:</text>
  <text x="20" y="116" fill="#6db33f" font-size="10" font-family="monospace">11111111 11111111 11111111 11111010</text>

  <text x="350" y="140" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">= -6 (sign bit set, two's complement)</text>
</svg>

`~` flips every bit across the type's full width — including the leading zeros a small positive number always has — which is why the result is negative for any non-negative input.

## 5. Runnable example

Scenario: a network-packet header parser that needs to clear specific option flags from a byte while preserving the others — the standard `& ~BIT` pattern, extended to a subnet-mask calculation (a genuinely real-world use of `~`).

### Level 1 — Basic

```java
public class ComplementBasic {
    public static void main(String[] args) {
        int packetFlags = 0b1111_0000;   // some combination of option bits set
        int URGENT_BIT = 0b0001_0000;

        System.out.println("Before: " + Integer.toBinaryString(packetFlags));
        int cleared = packetFlags & ~URGENT_BIT;   // clear just the URGENT bit
        System.out.println("After:  " + Integer.toBinaryString(cleared));
    }
}
```

**How to run:** `java ComplementBasic.java`

`~URGENT_BIT` produces a mask that is all `1`s except at the `URGENT_BIT` position, which is `0`. ANDing `packetFlags` with this mask forces the `URGENT_BIT` position to `0` in the result (since anything AND `0` is `0`), while every other bit of `packetFlags` passes through unchanged (since anything AND `1` is itself) — this is the canonical "clear one specific bit" idiom.

### Level 2 — Intermediate

Same header parser, now clearing multiple bits at once using a combined mask, and demonstrating the common mistake of forgetting `~` operates on the full 32-bit width (leading to a mask that accidentally also clears bits you didn't intend, if misused with a narrower type without care).

```java
public class ComplementIntermediate {
    public static void main(String[] args) {
        int packetFlags = 0b1111_1111;
        int URGENT = 0b0001_0000, RESERVED = 0b0010_0000;

        // Clear BOTH bits at once by combining them with | before complementing
        int combinedMask = ~(URGENT | RESERVED);
        int cleared = packetFlags & combinedMask;
        System.out.println("Before: " + Integer.toBinaryString(packetFlags));
        System.out.println("After:  " + Integer.toBinaryString(cleared));   // both bits cleared

        // Demonstrating the full-width nature of ~ explicitly
        byte smallFlag = 0b0001;
        int wideComplement = ~smallFlag;    // smallFlag promoted to int FIRST, then complemented
        System.out.println("~ of a promoted byte: " + wideComplement);    // large negative number, not a small byte pattern
    }
}
```

**How to run:** `java ComplementIntermediate.java`

`~(URGENT | RESERVED)` first combines both target bits into one mask with `|`, then complements the *combined* mask — this correctly produces a mask that is `0` at both target positions and `1` everywhere else, clearing both bits in a single AND operation. The `byte smallFlag` example makes the full-width behavior explicit: unary numeric promotion widens `smallFlag` to `int` *before* `~` ever runs, so the complement operates across all 32 bits of that promoted `int`, producing a large negative number rather than an 8-bit pattern — a reminder that `~` (like all the bitwise/arithmetic unary and binary operators) never actually operates on a `byte`-width value directly.

### Level 3 — Advanced

A genuinely practical use of `~`: computing a subnet mask's **wildcard mask** (the complement of a subnet mask, used in networking access-control lists and routing) from a given prefix length, and using it to compute a network's broadcast address.

```java
public class ComplementAdvanced {

    static int subnetMaskFromPrefix(int prefixLength) {
        // A /24 mask is 24 leading 1 bits followed by 8 zero bits: 11111111 11111111 11111111 00000000
        if (prefixLength == 0) return 0;
        return 0xFFFFFFFF << (32 - prefixLength);
    }

    public static void main(String[] args) {
        int prefixLength = 24;   // e.g., a /24 network like 192.168.1.0/24
        int subnetMask = subnetMaskFromPrefix(prefixLength);
        int wildcardMask = ~subnetMask;   // complement: the "host bits" mask

        System.out.printf("Subnet mask (/%d):   %s%n", prefixLength, formatAsIp(subnetMask));
        System.out.printf("Wildcard mask:        %s%n", formatAsIp(wildcardMask));

        // Compute the broadcast address: network address OR'd with the wildcard mask
        int networkAddress = ipToInt(192, 168, 1, 0);
        int broadcastAddress = networkAddress | wildcardMask;
        System.out.println("Network address:   " + formatAsIp(networkAddress));
        System.out.println("Broadcast address: " + formatAsIp(broadcastAddress));
    }

    static int ipToInt(int a, int b, int c, int d) {
        return (a << 24) | (b << 16) | (c << 8) | d;
    }

    static String formatAsIp(int ip) {
        return ((ip >> 24) & 0xFF) + "." + ((ip >> 16) & 0xFF) + "." + ((ip >> 8) & 0xFF) + "." + (ip & 0xFF);
    }
}
```

**How to run:** `java ComplementAdvanced.java`

`subnetMaskFromPrefix(24)` builds a mask with 24 leading `1` bits by shifting `0xFFFFFFFF` (all `1`s) left by `32 - 24 = 8` positions, which pushes 8 zero bits in from the right, yielding `255.255.255.0` when formatted as an IP address. `~subnetMask` computes the wildcard mask — the complement flips every `1` to `0` and every `0` to `1`, so the 24 leading `1`s become `0`s and the trailing 8 `0`s become `1`s, giving `0.0.0.255`, which represents exactly the "host portion" bits of the address (the bits that vary between individual hosts on the same subnet). `networkAddress | wildcardMask` then sets every host bit to `1` (via OR with the wildcard mask, which has `1`s exactly in the host-bit positions), computing the broadcast address `192.168.1.255` — this is a genuinely standard real-world networking calculation that directly relies on `~`'s bit-flipping behavior.

## 6. Walkthrough

Trace `wildcardMask = ~subnetMask` where `subnetMask` represents `255.255.255.0`:

**Subnet mask in binary.** `255.255.255.0` as a 32-bit integer is `11111111 11111111 11111111 00000000` — 24 leading `1` bits (the "network" portion) followed by 8 trailing `0` bits (the "host" portion).

**Complement, bit by bit.** `~` flips every one of the 32 bits independently. Each of the 24 leading `1`s becomes `0`, and each of the 8 trailing `0`s becomes `1`. The result is `00000000 00000000 00000000 11111111`.

**Interpreting the result.** This bit pattern, `00000000 00000000 00000000 11111111`, is exactly `0.0.0.255` when split into four 8-bit octets and formatted as an IP address — the wildcard mask correctly identifies the last octet as the "host" portion that varies across individual machines in the subnet, and the first three octets as fixed (network) bits.

```
subnetMask:    11111111 11111111 11111111 00000000   (255.255.255.0)
                       ~ (flip every bit)
wildcardMask:  00000000 00000000 00000000 11111111   (0.0.0.255)
```

**Using it to compute the broadcast address.** `networkAddress | wildcardMask` takes `192.168.1.0` (binary `11000000 10101000 00000001 00000000`) and ORs it with the wildcard mask (`00000000 00000000 00000000 11111111`). Wherever the wildcard mask has a `1` (the last octet), the OR forces that bit to `1` regardless of the network address's original bit there; wherever the wildcard mask has a `0` (the first three octets), the OR leaves the network address's bits unchanged. The result, `11000000 10101000 00000001 11111111`, is `192.168.1.255` — the broadcast address, with every host bit set to its maximum value.

## 7. Gotchas & takeaways

> **`~` flips every bit across the type's full width, not just the "visible" low bits of a small number.** `~5` is not some small 3-bit pattern; it is a 32-bit value with 29 of its upper bits also flipped, which prints as `-6` when interpreted as a signed `int`. Always think of `~` as operating on the entire 32-bit (or 64-bit for `long`) representation.

> **`~x` is mathematically equivalent to `-x - 1`, a direct consequence of two's-complement representation.** This identity is occasionally useful for reasoning about `~`'s numeric effect, but the far more common practical use is building an inverse bitmask for clearing specific bits with `&`.

- `~` flips every bit of its integer operand; `byte`/`short`/`char` operands are promoted to `int` first (unary numeric promotion), so the complement always spans at least 32 bits.
- `flags & ~BIT` is the standard idiom for clearing one or more specific bits while leaving all others unchanged.
- `~x == -x - 1` for any integer `x`, a direct consequence of two's-complement arithmetic.
- Computing a network's wildcard mask (`~subnetMask`) and using it to derive a broadcast address (`network | wildcardMask`) is a genuine, standard real-world application of `~` in networking code.
