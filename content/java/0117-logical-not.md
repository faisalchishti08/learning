---
card: java
gi: 117
slug: logical-not
title: Logical NOT !
---

## 1. What it is

`!` is a unary operator that inverts a single `boolean` operand: `!true` is `false`, and `!false` is `true`. It is the only logical negation operator in Java (there is no "not" version of `&`/`|` beyond negating the whole expression), and it applies to exactly one operand, unlike `&&`/`||`, which combine two. `!` has very high precedence — higher than the relational, arithmetic, and logical binary operators — so it binds tightly to whatever immediately follows it, which matters when negating a larger expression.

```java
boolean isReady = false;
System.out.println(!isReady);       // true

int x = 5;
System.out.println(!(x > 3));        // false — parentheses needed: ! binds to "x" alone otherwise... 
// !x > 3 would not even compile, since ! requires a boolean operand and x is an int
```

Because `!` binds so tightly, negating a multi-part condition almost always requires parentheses around the whole condition: `!(a && b)` is very different from `!a && b` (this distinction is formalized by De Morgan's laws, covered in the walkthrough below).

## 2. Why & when

`!` is used to invert conditions, flip flags, and express "the opposite case" cleanly:

- Toggling state: `enabled = !enabled;` flips a boolean flag.
- Inverting a guard: `if (!list.isEmpty())` instead of restructuring the whole branch to check emptiness first.
- Negating a compound condition to express its opposite: `if (!(age >= 18 && hasConsent))` denies access unless both conditions hold.

The most common `!`-related bug is misapplying De Morgan's laws by hand — writing `!a && !b` when `!(a && b)` (which is equivalent to `!a || !b`) was actually intended, or vice versa. Because `!` binds tightly, it is also easy to forget the parentheses needed to negate a whole compound expression rather than just its first term.

## 3. Core concept

```java
public class LogicalNotDemo {
    public static void main(String[] args) {
        boolean isReady = false;
        System.out.println("!isReady: " + !isReady);   // true

        // Toggling a flag
        boolean flag = true;
        flag = !flag;
        System.out.println("toggled flag: " + flag);    // false

        // High precedence: ! binds tightly, parentheses needed for compound expressions
        int age = 20;
        boolean hasConsent = false;
        System.out.println("!(age >= 18 && hasConsent): " + !(age >= 18 && hasConsent));  // true (consent missing)

        // De Morgan's law demonstration: !(a && b) == (!a || !b)
        boolean a = true, b = false;
        System.out.println("!(a && b):     " + !(a && b));       // true
        System.out.println("!a || !b:      " + (!a || !b));       // true — equivalent

        // De Morgan's law: !(a || b) == (!a && !b)
        System.out.println("!(a || b):     " + !(a || b));        // false
        System.out.println("!a && !b:      " + (!a && !b));        // false — equivalent

        // Double negation cancels out
        boolean value = true;
        System.out.println("!!value: " + !!value);   // true, same as value
    }
}
```

## 4. Diagram

<svg viewBox="0 0 700 175" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="De Morgan's laws diagram: not of a AND b equals not a OR not b, and not of a OR b equals not a AND not b. Negating a compound AND flips it to OR with each term negated, and vice versa.">
  <rect x="8" y="8" width="684" height="159" rx="8" fill="#0d1117"/>
  <text x="350" y="24" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">De Morgan's laws — negating a compound condition flips the connective</text>

  <rect x="16" y="34" width="330" height="118" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="181" y="52" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">!(a &amp;&amp; b)  ==  !a || !b</text>
  <text x="30" y="76" fill="#e6edf3" font-size="8" font-family="sans-serif">"NOT (both true)"</text>
  <text x="30" y="94" fill="#e6edf3" font-size="8" font-family="sans-serif">is the same as</text>
  <text x="30" y="112" fill="#79c0ff" font-size="8" font-family="sans-serif">"at least one is false"</text>
  <text x="30" y="134" fill="#6db33f" font-size="7.5" font-family="sans-serif">AND flips to OR; each term negates.</text>

  <rect x="356" y="34" width="328" height="118" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="520" y="52" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">!(a || b)  ==  !a &amp;&amp; !b</text>
  <text x="370" y="76" fill="#e6edf3" font-size="8" font-family="sans-serif">"NOT (at least one true)"</text>
  <text x="370" y="94" fill="#e6edf3" font-size="8" font-family="sans-serif">is the same as</text>
  <text x="370" y="112" fill="#79c0ff" font-size="8" font-family="sans-serif">"both are false"</text>
  <text x="370" y="134" fill="#6db33f" font-size="7.5" font-family="sans-serif">OR flips to AND; each term negates.</text>
</svg>

Negating a compound condition flips its connective (`&&` ↔ `||`) and negates each individual term.

## 5. Runnable example

Scenario: an access-control check for a document-sharing feature — first written with a compound condition, then negated using De Morgan's law by hand (a common but error-prone practice), then verified for correctness against every input combination.

### Level 1 — Basic

```java
public class AccessBasic {

    static boolean canView(boolean isOwner, boolean isSharedWithMe) {
        return isOwner || isSharedWithMe;
    }

    public static void main(String[] args) {
        System.out.println("Owner, not shared: " + canView(true, false));    // true
        System.out.println("Not owner, shared: " + canView(false, true));     // true
        System.out.println("Neither:            " + canView(false, false));    // false

        // Using ! to express the inverse directly, rather than restructuring the method
        boolean isOwner = false, isSharedWithMe = false;
        if (!canView(isOwner, isSharedWithMe)) {
            System.out.println("Access denied.");
        }
    }
}
```

**How to run:** `java AccessBasic.java`

`!canView(isOwner, isSharedWithMe)` simply negates the whole boolean result returned by `canView` — this is the safest, clearest way to express "the opposite of this condition" without manually reasoning about De Morgan's law at all, since `!` here applies to a single boolean value (the method's return), not a compound expression that needs restructuring.

### Level 2 — Intermediate

Same access check, now inlining the condition directly (without the helper method) and manually negating it using De Morgan's law — demonstrating the equivalence, and a common mistake when doing this transformation by hand.

```java
public class AccessIntermediate {
    public static void main(String[] args) {
        boolean isOwner = false, isSharedWithMe = false;

        // Original condition, inlined
        boolean canView = isOwner || isSharedWithMe;

        // Correct manual negation via De Morgan's law: !(a || b) == !a && !b
        boolean correctlyDenied = !isOwner && !isSharedWithMe;

        // COMMON MISTAKE: negating each term but keeping the same connective
        boolean mistakenlyDenied = !isOwner || !isSharedWithMe;   // WRONG for expressing "not canView"

        System.out.println("canView:            " + canView);              // false
        System.out.println("!canView (direct):   " + !canView);             // true
        System.out.println("correctlyDenied:      " + correctlyDenied);      // true — matches !canView
        System.out.println("mistakenlyDenied:     " + mistakenlyDenied);     // ALSO true here, by coincidence!

        // Prove the mistake with a DIFFERENT input where they diverge
        isOwner = true; isSharedWithMe = false;
        canView = isOwner || isSharedWithMe;
        correctlyDenied = !isOwner && !isSharedWithMe;
        mistakenlyDenied = !isOwner || !isSharedWithMe;
        System.out.println("---");
        System.out.println("canView:            " + canView);               // true
        System.out.println("!canView (direct):   " + !canView);              // false
        System.out.println("correctlyDenied:      " + correctlyDenied);       // false — matches !canView, correct
        System.out.println("mistakenlyDenied:     " + mistakenlyDenied);      // true — WRONG, diverges from !canView!
    }
}
```

**How to run:** `java AccessIntermediate.java`

With `isOwner=false, isSharedWithMe=false`, both the correct De Morgan's negation (`!isOwner && !isSharedWithMe`) and the mistaken one (`!isOwner || !isSharedWithMe`) happen to agree, because negating two `false` values gives two `true` values, and `true && true` equals `true || true`. The bug only becomes visible with a *different* input: `isOwner=true, isSharedWithMe=false` makes `canView` `true` (the owner can view), so the correct negation `correctlyDenied` should be `false` — and it is. But `mistakenlyDenied` (which wrongly kept `||` instead of flipping to `&&`) evaluates `!true || !false` = `false || true` = `true`, incorrectly claiming access should be denied when the owner clearly should have access. This demonstrates why De Morgan's transformation must flip the connective, not just negate the individual terms.

### Level 3 — Advanced

Same access-control logic, now with a three-term compound condition (owner, shared, or admin override) and a runtime self-check that exhaustively verifies `!compound == deMorganNegation` across every combination of inputs, catching the class of bug from Level 2 automatically rather than relying on manual reasoning.

```java
public class AccessAdvanced {

    static boolean canView(boolean isOwner, boolean isSharedWithMe, boolean isAdmin) {
        return isOwner || isSharedWithMe || isAdmin;
    }

    static boolean cannotView(boolean isOwner, boolean isSharedWithMe, boolean isAdmin) {
        // De Morgan's law extends to any number of terms: !(a || b || c) == !a && !b && !c
        return !isOwner && !isSharedWithMe && !isAdmin;
    }

    public static void main(String[] args) {
        boolean[] values = { true, false };
        int mismatches = 0;

        for (boolean owner : values) {
            for (boolean shared : values) {
                for (boolean admin : values) {
                    boolean view = canView(owner, shared, admin);
                    boolean deniedDirect = !view;
                    boolean deniedManual = cannotView(owner, shared, admin);
                    boolean matches = deniedDirect == deniedManual;
                    if (!matches) mismatches++;
                    System.out.printf("owner=%-5b shared=%-5b admin=%-5b -> canView=%-5b !canView=%-5b cannotView=%-5b %s%n",
                        owner, shared, admin, view, deniedDirect, deniedManual, matches ? "OK" : "MISMATCH");
                }
            }
        }
        System.out.println("Total mismatches: " + mismatches);  // 0 — De Morgan's law holds for all 8 combinations
    }
}
```

**How to run:** `java AccessAdvanced.java`

This exhaustively tests all `2^3 = 8` combinations of the three boolean inputs, comparing `!canView(...)` (the trusted, direct negation) against `cannotView(...)` (the manually De-Morgan'd, three-term version `!owner && !shared && !admin`) for every combination — since three-term boolean logic is small enough to brute-force exhaustively, this kind of self-check is a practical way to verify a manual De Morgan transformation is correct without having to trust hand-derived algebra, especially valuable as the number of terms grows and manual reasoning becomes more error-prone.

## 6. Walkthrough

Trace the mismatch scenario from Level 2 in detail, `isOwner=true, isSharedWithMe=false`:

**Evaluate `canView`.** `isOwner || isSharedWithMe` = `true || false`. Because `||` short-circuits on a `true` left operand, the result is `true` without even needing `isSharedWithMe`'s value, though here it's shown for clarity — either way, `canView = true`.

**Evaluate the direct negation.** `!canView` = `!true` = `false`. This is the ground truth: the owner should have access, so "cannot view" should be `false`.

**Evaluate the correct De Morgan's version.** `!isOwner && !isSharedWithMe` = `!true && !false` = `false && true`. Because `&&` short-circuits on a `false` left operand, the result is `false` immediately. This matches the ground truth.

**Evaluate the mistaken version.** `!isOwner || !isSharedWithMe` = `!true || !false` = `false || true`. Because the left operand is `false`, `||` evaluates the right operand: `true`. The overall result is `true` — but the ground truth says "cannot view" should be `false`. This is the mismatch: the mistaken formula incorrectly reports the owner as denied access.

```
isOwner=true, isSharedWithMe=false

canView = isOwner || isSharedWithMe = true || false = true
!canView = false                                          <- ground truth: owner CAN view

Correct:   !isOwner && !isSharedWithMe = false && true = false   <- matches ground truth ✓
Mistaken:  !isOwner || !isSharedWithMe = false || true  = true    <- WRONG, contradicts ground truth ✗
```

**Why the mistake happens.** The mistaken version keeps the original `||` connective but negates each individual term — this looks superficially like "the same shape, just negated," but De Morgan's law specifically requires flipping `||` to `&&` (or `&&` to `||`) *at the same time* as negating each term. Skipping the connective flip is the single most common error when manually negating compound boolean expressions.

## 7. Gotchas & takeaways

> **De Morgan's law requires flipping the connective, not just negating each term.** `!(a || b)` equals `!a && !b`, not `!a || !b`. Getting this wrong produces a formula that happens to agree with the correct one for *some* inputs (making the bug easy to miss in casual testing) but diverges for others.

> **`!` has very high precedence and binds to the smallest possible operand.** `!a && b` means `(!a) && b`, not `!(a && b)` — always parenthesize the full expression you intend to negate: `!(a && b)`.

- `!` inverts a single `boolean` value; it has no direct "combine two operands" form.
- Prefer negating a whole named condition or method result (`!isValid()`) over manually re-deriving a negated compound expression with De Morgan's law, since the latter is error-prone.
- If you must manually negate a compound expression, remember: `!(a && b) == !a || !b`, and `!(a || b) == !a && !b` — the connective always flips.
- For a small, fixed number of boolean inputs, exhaustively testing every combination is a cheap and reliable way to verify a hand-derived negation is correct.
