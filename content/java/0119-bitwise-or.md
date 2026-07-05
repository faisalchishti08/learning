---
card: java
gi: 119
slug: bitwise-or
title: Bitwise OR |
---

## 1. What it is

`|` mirrors `&` but with the opposite combining rule. On integer types, `|` performs a **bitwise OR**: each output bit is `1` if *either* (or both) of the corresponding input bits is `1`, and `0` only when both inputs are `0`. On `boolean` operands, `|` performs a **non-short-circuiting logical OR** — the same `true`/`false` result as `||`, but (unlike `||`) both operands are always evaluated, even if the left one is already `true`.

```java
int a = 0b1100;   // 12
int b = 0b1010;   // 10
int result = a | b;   // 0b1110 = 14 — a 1 survives wherever EITHER operand has a 1
System.out.println(result);

boolean x = true;
boolean y = someExpensiveCheck();
boolean r = x | y;   // y IS evaluated even though x is already true (no short-circuit)
```

Bitwise `|` is the standard way to **combine multiple independent flags into a single bitmask**, since setting a bit in the result requires only that at least one of the source values already had it set — this makes `|` the natural "union" operator for sets of flags represented as bits.

## 2. Why & when

`|` is used constantly wherever multiple independent boolean options need to be packed into one compact value:

- Combining permission flags: `int permissions = READ | WRITE;` sets both bits at once.
- Building a combined filter mask: `int events = CLICK | HOVER | SCROLL;` to subscribe to multiple event types.
- Setting a specific bit without disturbing others: `flags |= SOME_BIT;` (using the compound-assignment form) turns on one bit while leaving every other bit in `flags` unchanged, because OR-ing any bit with `0` (its own unchanged value) leaves it as-is, while OR-ing with `1` forces it on.

Just like `&`, `boolean |` is rare to use deliberately (`||` is almost always preferred for plain conditionals because of short-circuiting), but it exists and behaves consistently with the integer form.

## 3. Core concept

```java
public class BitwiseOrDemo {
    public static void main(String[] args) {
        int a = 0b1100;  // 12
        int b = 0b1010;  // 10
        System.out.println("a | b = " + (a | b) + " (binary: " + Integer.toBinaryString(a | b) + ")");  // 14, "1110"

        // Combining flags into one bitmask
        int READ = 0b001, WRITE = 0b010, EXEC = 0b100;
        int permissions = READ | WRITE;
        System.out.println("Combined permissions: " + Integer.toBinaryString(permissions));   // "11"

        // Setting a single bit without disturbing others (compound |=)
        int flags = 0b0010;
        flags |= 0b1000;   // turn on bit 3, leave bit 1 as it was
        System.out.println("After setting bit 3: " + Integer.toBinaryString(flags));   // "1010"

        // Non-short-circuiting boolean |
        boolean left = true;
        boolean right = logAndReturn(false);   // this call happens even though `left` is already true
        System.out.println("left | right = " + (left | right));
    }

    static boolean logAndReturn(boolean value) {
        System.out.println("  right operand evaluated");
        return value;
    }
}
```

## 4. Diagram

<svg viewBox="0 0 700 155" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Bitwise OR diagram: 12 in binary 1100 OR 10 in binary 1010, computed bit by bit, gives 1110 which is 14. A 1 survives at any bit position where at least one operand has a 1.">
  <rect x="8" y="8" width="684" height="139" rx="8" fill="#0d1117"/>
  <text x="350" y="24" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">0b1100 (12) | 0b1010 (10) — bit by bit, right to left</text>

  <text x="200" y="52" fill="#e6edf3" font-size="14" text-anchor="middle" font-family="monospace">1  1  0  0</text>
  <text x="200" y="74" fill="#e6edf3" font-size="14" text-anchor="middle" font-family="monospace">1  0  1  0</text>
  <line x1="130" y1="82" x2="270" y2="82" stroke="#8b949e" stroke-width="1.5"/>
  <text x="200" y="100" fill="#6db33f" font-size="14" text-anchor="middle" font-family="monospace">1  1  1  0</text>
  <text x="200" y="122" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">= 14 (a 1 survives if EITHER input has a 1)</text>

  <text x="500" y="52" fill="#8b949e" font-size="9" font-family="monospace">bit 3: 1 | 1 = 1</text>
  <text x="500" y="70" fill="#8b949e" font-size="9" font-family="monospace">bit 2: 1 | 0 = 1</text>
  <text x="500" y="88" fill="#8b949e" font-size="9" font-family="monospace">bit 1: 0 | 1 = 1</text>
  <text x="500" y="106" fill="#8b949e" font-size="9" font-family="monospace">bit 0: 0 | 0 = 0</text>
</svg>

`|` computes each output bit independently — a `1` survives wherever at least one input had a `1` in that exact position.

## 5. Runnable example

Scenario: a notification-preferences system where a user can opt into several independent channels (email, SMS, push) — a natural fit for combining flags with `|`, extended to building preferences incrementally and merging two users' preference sets.

### Level 1 — Basic

```java
public class NotificationBasic {
    static final int EMAIL = 0b001, SMS = 0b010, PUSH = 0b100;

    public static void main(String[] args) {
        int userPrefs = EMAIL | PUSH;   // user wants email and push, not SMS

        System.out.println("Preferences: " + Integer.toBinaryString(userPrefs));
        System.out.println("Email enabled: " + ((userPrefs & EMAIL) != 0));
        System.out.println("SMS enabled:   " + ((userPrefs & SMS) != 0));
        System.out.println("Push enabled:  " + ((userPrefs & PUSH) != 0));
    }
}
```

**How to run:** `java NotificationBasic.java`

`EMAIL | PUSH` combines the two independent flag bits into a single value: `0b001 | 0b100 = 0b101`. Checking each channel afterward uses `&` (from the previous topic) to test whether that specific bit survived in the combined mask — `EMAIL`'s bit is present (`0b101 & 0b001 = 0b001`, non-zero), `SMS`'s bit is not (`0b101 & 0b010 = 0b000`, zero).

### Level 2 — Intermediate

Same preferences system, now letting a user incrementally opt into channels one at a time using compound `|=`, and merging two users' preference sets to compute a combined "notify if either wants it" mask for a shared household account.

```java
public class NotificationIntermediate {
    static final int EMAIL = 0b001, SMS = 0b010, PUSH = 0b100;

    public static void main(String[] args) {
        int prefs = 0;                  // start with nothing enabled
        System.out.println("Start: " + Integer.toBinaryString(prefs));

        prefs |= EMAIL;                  // user opts into email
        System.out.println("After enabling email: " + Integer.toBinaryString(prefs));

        prefs |= PUSH;                    // user also opts into push
        System.out.println("After enabling push:  " + Integer.toBinaryString(prefs));

        prefs |= EMAIL;                    // re-enabling an already-set flag changes nothing
        System.out.println("After re-enabling email (no-op): " + Integer.toBinaryString(prefs));

        // Merge two household members' preferences: notify on a channel if EITHER wants it
        int userA = EMAIL;
        int userB = SMS | PUSH;
        int household = userA | userB;
        System.out.println("Household combined preferences: " + Integer.toBinaryString(household));
    }
}
```

**How to run:** `java NotificationIntermediate.java`

`prefs |= EMAIL` is shorthand for `prefs = prefs | EMAIL`, which turns on the `EMAIL` bit while leaving every other bit in `prefs` exactly as it was — OR-ing a bit that is already `0` with `EMAIL`'s `1` sets it to `1`, and OR-ing a bit that's already something else with `EMAIL`'s `0` (in the other bit positions) leaves it unchanged. Re-enabling `EMAIL` a second time (`prefs |= EMAIL` when the bit is already set) is idempotent: `1 | 1 = 1`, so nothing changes — a useful property showing `|=` is always safe to call repeatedly without needing to check if the flag is already set. `userA | userB` demonstrates using `|` directly as a "union" operator across two independent bitmasks, producing a combined mask with every bit that was set in either input.

### Level 3 — Advanced

Same system, now building a compact event-subscription bitmask from a variable-length list of requested channels (using `|` inside a loop, the idiomatic way to fold a collection of flags into one combined value), and demonstrating how `|` combined with a running accumulator differs from simply summing the flag values with `+` (which would double-count overlapping bits if the flags weren't perfectly distinct powers of two — a subtle correctness argument for why `|` is the right tool, not `+`).

```java
import java.util.*;

public class NotificationAdvanced {
    static final int EMAIL = 0b0001, SMS = 0b0010, PUSH = 0b0100, WEBHOOK = 0b1000;

    static int combineChannels(List<Integer> requestedChannels) {
        int combined = 0;
        for (int channel : requestedChannels) {
            combined |= channel;   // folds each channel's bit(s) into the accumulator
        }
        return combined;
    }

    public static void main(String[] args) {
        List<Integer> requests = List.of(EMAIL, PUSH, EMAIL, WEBHOOK);  // EMAIL requested twice, redundantly
        int combined = combineChannels(requests);
        System.out.println("Combined via |:  " + Integer.toBinaryString(combined));  // correctly de-duplicates EMAIL

        // Contrast: naively summing with + would double-count the duplicate EMAIL request
        int summed = 0;
        for (int channel : requests) summed += channel;
        System.out.println("Naively summed:  " + summed + " (binary: " + Integer.toBinaryString(summed) + ")");
        System.out.println("Combined value:  " + combined);
        System.out.println("Do they match?   " + (summed == combined));  // false — + double-counted EMAIL

        // Decode which channels are active in the correctly-combined mask
        String[] names = { "EMAIL", "SMS", "PUSH", "WEBHOOK" };
        int[] bits = { EMAIL, SMS, PUSH, WEBHOOK };
        System.out.print("Active channels: ");
        for (int i = 0; i < bits.length; i++) {
            if ((combined & bits[i]) != 0) System.out.print(names[i] + " ");
        }
        System.out.println();
    }
}
```

**How to run:** `java NotificationAdvanced.java`

`combineChannels` folds a list of requested channel flags into one accumulator using `|=` in a loop — because `|` is idempotent (`1 | 1 = 1`), requesting `EMAIL` twice in the input list has no different effect than requesting it once; the combined mask correctly represents "which distinct channels were requested at least once," which is exactly the union semantics wanted here. The naive `+`-based summation, in contrast, is *not* idempotent — adding `EMAIL`'s value (`1`) twice contributes `2` to the sum, which happens to collide with `SMS`'s bit value, corrupting the result into something that no longer represents a clean union of flags. This is the underlying reason bitwise flag combination always uses `|`, never `+`: `|` guarantees a stable, order-independent, duplicate-safe union, while `+` only works "by accident" when every flag is used at most once and the flags don't happen to sum into another flag's value.

## 6. Walkthrough

Trace `combineChannels(List.of(EMAIL, PUSH, EMAIL, WEBHOOK))` where `EMAIL=0b0001, PUSH=0b0100, WEBHOOK=0b1000`:

**Initialize.** `combined = 0` (`0b0000`).

**First iteration: `channel = EMAIL` (`0b0001`).** `combined |= EMAIL` computes `0b0000 | 0b0001 = 0b0001`. `combined` is now `0b0001`.

**Second iteration: `channel = PUSH` (`0b0100`).** `combined |= PUSH` computes `0b0001 | 0b0100 = 0b0101`. `combined` is now `0b0101`.

**Third iteration: `channel = EMAIL` again (`0b0001`).** `combined |= EMAIL` computes `0b0101 | 0b0001 = 0b0101`. Because bit 0 (`EMAIL`'s bit) was already `1`, OR-ing it with `1` again leaves it `1` — `combined` is unchanged at `0b0101`. This is the idempotence that makes duplicate requests harmless.

**Fourth iteration: `channel = WEBHOOK` (`0b1000`).** `combined |= WEBHOOK` computes `0b0101 | 0b1000 = 0b1101`. `combined` is now `0b1101`.

```
combined = 0000
| EMAIL   (0001) -> 0001
| PUSH    (0100) -> 0101
| EMAIL   (0001) -> 0101   (no change — bit already set)
| WEBHOOK (1000) -> 1101

final combined = 1101  (EMAIL, PUSH, WEBHOOK all set; SMS not set)
```

**Contrast with `+`.** Summing the same list with `+` instead: `0 + 1 + 4 + 1 + 8 = 14 = 0b1110`. This differs from the correct `0b1101` — the extra `EMAIL` contributed an additional `+1` that, combined with the first `EMAIL`'s `+1`, summed to `2` (`0b0010`), which is bit-identical to `SMS`'s flag value, falsely making it look like `SMS` was requested when it never was.

**Final output.** The program prints the correctly de-duplicated combined mask (`1101`), the incorrect summed value (`14`, which decodes to a different and wrong set of bits), confirms they don't match, and then decodes the correct mask into a human-readable list of active channel names: `EMAIL PUSH WEBHOOK`.

## 7. Gotchas & takeaways

> **Never use `+` to combine independent bit flags — use `|`.** `+` is not idempotent for repeated or overlapping flags, and a sum of flag values can accidentally equal a different, unrelated flag's value, corrupting the combined mask in a way that is very hard to spot by inspection.

> **`|` on `boolean` operands does not short-circuit — both sides are always evaluated,** just like `&`. Prefer `||` for ordinary conditionals to retain the short-circuit protection.

- Bitwise `|` on integers produces `1` in each bit position where at least one operand has `1` there — the standard tool for combining/union-ing independent flags.
- `flags |= BIT` sets a single bit without disturbing any other bit already in `flags`, and is safe to call repeatedly (idempotent).
- Folding a list of flags with `|=` in a loop correctly de-duplicates repeated or overlapping requests; folding with `+=` does not and can corrupt the result.
- Boolean `|` computes the same result as `||` but always evaluates both operands — prefer `||` unless you specifically need both sides evaluated regardless of the first result.
