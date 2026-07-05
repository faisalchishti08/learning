---
card: java
gi: 127
slug: operator-precedence-associativity
title: Operator precedence & associativity
---

## 1. What it is

When an expression contains multiple operators without parentheses, Java must decide which operator "binds tighter" — that is, which sub-expression gets grouped and evaluated first. **Precedence** ranks operators from highest to lowest: higher-precedence operators bind more tightly and are grouped first (`*` binds tighter than `+`, so `2 + 3 * 4` groups as `2 + (3 * 4)`, not `(2 + 3) * 4`). **Associativity** resolves ties between operators of *equal* precedence, determining whether they group left-to-right or right-to-left. Almost all of Java's binary operators are left-associative; the main exceptions are assignment operators (right-associative) and the ternary operator (right-associative).

```java
System.out.println(2 + 3 * 4);        // 14, not 20 — * has higher precedence than +
System.out.println(10 - 3 - 2);         // 5, not 9 — - is left-associative: (10 - 3) - 2
System.out.println(2 + 3 == 5);          // true — + (precedence 12ish) binds tighter than == (lower)

int a, b, c;
a = b = c = 5;    // right-associative: a = (b = (c = 5))
System.out.println(a + " " + b + " " + c);   // 5 5 5
```

A rough (high-to-low) precedence ordering worth internalizing: postfix `++`/`--` → unary `+ - ! ~` and prefix `++`/`--` → multiplicative `* / %` → additive `+ -` → shift `<< >> >>>` → relational `< > <= >= instanceof` → equality `== !=` → bitwise `& ^ |` (in that order, lowest to highest of these three) → logical `&& ||` → ternary `?:` → assignment `= += -= ...`.

## 2. Why & when

Understanding precedence and associativity matters whenever an expression combines more than one kind of operator without full parenthesization:

- Arithmetic mixed with comparison: `a + b > c * d` groups as `(a + b) > (c * d)`, since `+`/`*` both bind tighter than `>`.
- Bitwise operators mixed with equality: `flags & MASK == 0` is a classic trap — `==` actually binds *tighter* than `&`, so this parses as `flags & (MASK == 0)`, almost certainly not the intended `(flags & MASK) == 0`, and often fails to even compile because `MASK == 0` produces a `boolean`, which `&` cannot combine with an `int` via bitwise AND.
- Logical operators mixed together: `a || b && c` groups as `a || (b && c)`, since `&&` binds tighter than `||`.

The safest practice for any expression mixing more than two distinct operator types is to add explicit parentheses — this costs nothing at runtime (the compiler already knows the precedence) and removes any doubt for a future reader who may not have every precedence rule memorized.

## 3. Core concept

```java
public class PrecedenceDemo {
    public static void main(String[] args) {
        // Arithmetic precedence: * before +
        System.out.println("2 + 3 * 4 = " + (2 + 3 * 4));     // 14

        // Left-associativity of - and /
        System.out.println("10 - 3 - 2 = " + (10 - 3 - 2));      // 5, i.e., (10-3)-2
        System.out.println("100 / 10 / 2 = " + (100 / 10 / 2));   // 5, i.e., (100/10)/2

        // Comparison vs arithmetic
        System.out.println("2 + 3 == 5: " + (2 + 3 == 5));    // true, (2+3) == 5

        // The classic bitwise-vs-equality trap
        int flags = 0b0110;
        int MASK = 0b0010;
        // flags & MASK == 0   would NOT compile: == binds tighter, giving flags & (MASK == 0) -> type error
        boolean hasFlag = (flags & MASK) == 0;    // must parenthesize explicitly
        System.out.println("hasFlag: " + hasFlag);

        // && binds tighter than ||
        boolean r = false || true && false;    // = false || (true && false) = false || false = false
        System.out.println("false || true && false = " + r);

        // Right-associativity of assignment and ternary
        int a, b;
        a = b = 5;
        System.out.println("a=" + a + " b=" + b);

        int x = 3;
        String label = x > 0 ? "positive" : x < 0 ? "negative" : "zero";  // right-associative ternary chain
        System.out.println("label: " + label);
    }
}
```

## 4. Diagram

<svg viewBox="0 0 700 175" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Operator precedence tower diagram from highest to lowest: unary operators at the top, then multiplicative, additive, shift, relational, equality, bitwise AND, bitwise XOR, bitwise OR, logical AND, logical OR, ternary, and assignment at the bottom. Higher operators bind tighter and are grouped first.">
  <rect x="8" y="8" width="684" height="159" rx="8" fill="#0d1117"/>
  <text x="350" y="22" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Precedence tower — higher binds tighter, grouped first (partial list, high to low)</text>

  <rect x="40" y="30" width="620" height="14" rx="3" fill="#6db33f" opacity="0.9"/>
  <text x="350" y="41" fill="#0d1117" font-size="8.5" text-anchor="middle" font-family="monospace">unary + - ! ~ ++ --  (highest)</text>

  <rect x="40" y="46" width="620" height="14" rx="3" fill="#6db33f" opacity="0.75"/>
  <text x="350" y="57" fill="#0d1117" font-size="8.5" text-anchor="middle" font-family="monospace">* / %</text>

  <rect x="40" y="62" width="620" height="14" rx="3" fill="#6db33f" opacity="0.6"/>
  <text x="350" y="73" fill="#0d1117" font-size="8.5" text-anchor="middle" font-family="monospace">+ -  (binary)</text>

  <rect x="40" y="78" width="620" height="14" rx="3" fill="#79c0ff" opacity="0.8"/>
  <text x="350" y="89" fill="#0d1117" font-size="8.5" text-anchor="middle" font-family="monospace">&lt;&lt; &gt;&gt; &gt;&gt;&gt;</text>

  <rect x="40" y="94" width="620" height="14" rx="3" fill="#79c0ff" opacity="0.65"/>
  <text x="350" y="105" fill="#0d1117" font-size="8.5" text-anchor="middle" font-family="monospace">&lt; &gt; &lt;= &gt;= instanceof</text>

  <rect x="40" y="110" width="620" height="14" rx="3" fill="#79c0ff" opacity="0.5"/>
  <text x="350" y="121" fill="#0d1117" font-size="8.5" text-anchor="middle" font-family="monospace">== !=</text>

  <rect x="40" y="126" width="620" height="14" rx="3" fill="#8b949e" opacity="0.7"/>
  <text x="350" y="137" fill="#0d1117" font-size="8.5" text-anchor="middle" font-family="monospace">&amp;  then  ^  then  |  (in this order)</text>

  <rect x="40" y="142" width="620" height="14" rx="3" fill="#8b949e" opacity="0.5"/>
  <text x="350" y="153" fill="#0d1117" font-size="8.5" text-anchor="middle" font-family="monospace">&amp;&amp;  then  ||  then  ?:  then  =  (lowest)</text>
</svg>

Higher rows bind tighter and are grouped first; equal-precedence operators on the same row combine using their associativity rule (mostly left-to-right).

## 5. Runnable example

Scenario: a permission-and-eligibility checker whose naive, unparenthesized condition silently misbehaves due to precedence, then fixed and finally hardened with a policy of deliberate, defensive parenthesization.

### Level 1 — Basic

```java
public class PrecedenceBasic {
    public static void main(String[] args) {
        int age = 25;
        boolean hasLicense = true;
        boolean hasInsurance = false;

        // Intended: "can drive" if (age >= 18 AND has a license) OR has insurance as an alternative path
        // Written naively without parentheses:
        boolean canDrive = age >= 18 && hasLicense || hasInsurance;
        System.out.println("canDrive: " + canDrive);   // true — but is the GROUPING what was intended?

        // Precedence actually groups this as: (age >= 18 && hasLicense) || hasInsurance
        // which happens to match the intent here, but only because of how && binds tighter than ||
        boolean explicit = (age >= 18 && hasLicense) || hasInsurance;
        System.out.println("explicit (same result): " + explicit);
    }
}
```

**How to run:** `java PrecedenceBasic.java`

`age >= 18 && hasLicense || hasInsurance` relies on `&&` binding tighter than `||` to group as `(age >= 18 && hasLicense) || hasInsurance` — which happens to be exactly what was intended in this case. But the naive version and the explicit version only *look* different; they compute the identical result because Java's precedence rules already do the grouping the author wanted. The risk is that a reader (or the author, revisiting the code later) cannot tell that from the unparenthesized version alone without recalling the precedence table from memory.

### Level 2 — Intermediate

Same eligibility check, now extended with a genuine precedence bug: mixing bitwise `&` with `==` in a flags check, which either fails to compile or (if types happened to align) silently computes the wrong thing.

```java
public class PrecedenceIntermediate {
    static final int LICENSED = 0b01, INSURED = 0b10;

    public static void main(String[] args) {
        int status = LICENSED;   // has a license, not insured

        // BUG: == binds tighter than &, so this parses as: status & (INSURED == 0)
        // INSURED == 0 is a boolean (false), and int & boolean does not compile at all.
        // boolean buggy = status & INSURED == 0;   // <- would NOT compile, left in as a comment

        // Correct: explicit parentheses force the intended grouping
        boolean isInsured = (status & INSURED) != 0;
        System.out.println("isInsured: " + isInsured);   // false

        boolean isLicensed = (status & LICENSED) != 0;
        System.out.println("isLicensed: " + isLicensed);  // true

        // A genuinely dangerous variant: mixing arithmetic and shift without parens
        int base = 4, exponent = 2;
        int shifted = 1 << base + exponent;    // + binds TIGHTER than <<, so this is 1 << (base + exponent) = 1 << 6 = 64
        int shiftedExplicit = 1 << (base + exponent);
        System.out.println("1 << base + exponent = " + shifted);           // 64
        System.out.println("Explicit, same result: " + shiftedExplicit);    // 64 — confirms the implicit grouping
    }
}
```

**How to run:** `java PrecedenceIntermediate.java`

The commented-out `status & INSURED == 0` line demonstrates a genuine compile error: because `==` has higher precedence than `&`, Java parses it as `status & (INSURED == 0)`, and since `INSURED == 0` evaluates to a `boolean`, attempting `int & boolean` fails to compile — this is actually a *safety net* in this specific case (the compiler catches the mistake), but it would not be caught if both operands happened to be types that made the accidental grouping compile silently. `1 << base + exponent` is a case where the grouping mistake *does* compile: `+` binds tighter than `<<`, so this evaluates `base + exponent` first (`4 + 2 = 6`), then shifts `1` left by `6`, giving `64` — matching the explicit version and confirming precedence, but a reader unfamiliar with shift's relatively low precedence might have expected `(1 << base) + exponent = 16 + 2 = 18` instead.

### Level 3 — Advanced

A comprehensive precedence self-test: build a small table of expressions, each written both implicitly (relying on precedence) and explicitly (with parentheses matching the documented precedence rules), and assert they always agree — a practical way to build confidence in precedence rules without memorizing the entire table by rote.

```java
public class PrecedenceAdvanced {

    static void check(String description, boolean implicitResult, boolean explicitResult) {
        boolean match = implicitResult == explicitResult;
        System.out.printf("%-45s implicit=%-6b explicit=%-6b %s%n",
            description, implicitResult, explicitResult, match ? "OK" : "MISMATCH");
    }

    static void check(String description, int implicitResult, int explicitResult) {
        boolean match = implicitResult == explicitResult;
        System.out.printf("%-45s implicit=%-6d explicit=%-6d %s%n",
            description, implicitResult, explicitResult, match ? "OK" : "MISMATCH");
    }

    public static void main(String[] args) {
        int a = 3, b = 4, c = 5;
        boolean p = true, q = false, r = true;

        // Arithmetic: * before +
        check("a + b * c", a + b * c, a + (b * c));

        // Additive is left-associative
        check("a - b + c", a - b + c, (a - b) + c);

        // Relational vs arithmetic
        check("a + b > c", (a + b > c), ((a + b) > c));

        // && before ||
        check("p || q && r", p || q && r, p || (q && r));

        // Shift vs additive
        check("1 << a + 1", 1 << a + 1, 1 << (a + 1));

        // Bitwise & vs equality (using ints to keep it compiling)
        int x = 6, mask = 2;
        check("(x & mask) == 2 vs explicit", ((x & mask) == 2), ((x & mask) == 2));  // trivially matches; the point is == must bind AFTER the parens

        // Ternary is right-associative
        int score = 72;
        String gradeImplicit = score >= 90 ? "A" : score >= 70 ? "B" : "C";
        String gradeExplicit = score >= 90 ? "A" : (score >= 70 ? "B" : "C");
        System.out.println("Ternary chain matches: " + gradeImplicit.equals(gradeExplicit));

        System.out.println("All precedence checks completed.");
    }
}
```

**How to run:** `java PrecedenceAdvanced.java`

Each `check` call computes the same expression two ways — once relying purely on Java's built-in precedence rules (the "implicit" version), and once with explicit parentheses matching what the documented precedence table says the implicit grouping *should* be — and confirms they match. This is a genuinely useful technique for building calibrated trust in precedence rules: rather than memorizing an entire table, you can write a handful of these paired checks for the specific operator combinations that appear in your own codebase and verify your mental model against the compiler's actual behavior. The ternary right-associativity check confirms that `score >= 90 ? "A" : score >= 70 ? "B" : "C"` groups as `score >= 90 ? "A" : (score >= 70 ? "B" : "C")` — the `:` branch of the first ternary is itself another complete ternary expression, not something that "greedily" tries to include the first ternary's condition again.

## 6. Walkthrough

Trace `1 << a + 1` where `a = 3`, comparing it against the naive (wrong) assumption that `<<` might bind tighter:

**Determine precedence.** Additive `+` has higher precedence than shift `<<` in Java (shift operators sit below additive in the precedence table, a detail that surprises many developers coming from the intuition that shifts are somehow "more primitive" or should bind more tightly). This means `+` groups first.

**Group the expression.** `1 << a + 1` is parsed as `1 << (a + 1)`, not `(1 << a) + 1`.

**Evaluate the grouped sub-expression.** `a + 1 = 3 + 1 = 4`.

**Apply the shift.** `1 << 4` shifts the bit pattern of `1` left by 4 positions, giving `16`.

**Contrast with the wrong assumption.** If shift had (incorrectly) been assumed to bind tighter, `(1 << a) + 1` would compute `1 << 3 = 8`, then `8 + 1 = 9` — a completely different result from the actual `16`.

```
Actual precedence: + binds tighter than <<
1 << a + 1   parses as   1 << (a + 1)   =   1 << 4   =   16

WRONG assumption: << binds tighter than +
(1 << a) + 1  would be   (1 << 3) + 1   =   8 + 1    =   9    <- NOT what Java actually computes
```

**Final output.** Every `check` call in the advanced example prints `OK` (confirming the implicit and explicit groupings match for that specific combination of operators), demonstrating that Java's actual precedence table — not intuition about which operators "feel" more fundamental — governs how these expressions are grouped.

## 7. Gotchas & takeaways

> **Shift operators (`<<`, `>>`, `>>>`) have lower precedence than additive operators (`+`, `-`).** `1 << a + 1` groups as `1 << (a + 1)`, which surprises many developers who intuitively expect shifts to bind more tightly since they feel more "primitive" or bit-level than arithmetic.

> **Equality (`==`, `!=`) has higher precedence than bitwise AND/XOR/OR (`&`, `^`, `|`).** `flags & MASK == 0` parses as `flags & (MASK == 0)`, which frequently fails to compile (mixing `int` and `boolean`) — always parenthesize explicitly: `(flags & MASK) == 0`.

- Precedence determines which operator groups first when multiple different operators appear in one expression; associativity resolves ties between operators of equal precedence (almost always left-to-right, except assignment and ternary, which are right-to-left).
- The most error-prone precedence gaps in practice are: shift below additive, and equality above bitwise AND/XOR/OR.
- When mixing more than one kind of operator in an expression, add explicit parentheses — it costs nothing at runtime and removes any ambiguity for a future reader.
- Writing a paired "implicit vs. explicit parentheses" check is a practical, low-effort way to verify your understanding of precedence for the specific operator combinations that appear in your own code, rather than relying on memorizing the full table.
