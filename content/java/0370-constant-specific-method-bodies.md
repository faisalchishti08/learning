---
card: java
gi: 370
slug: constant-specific-method-bodies
title: Constant-specific method bodies
---

## 1. What it is

A **constant-specific method body** lets an individual enum constant override an abstract method with its own implementation, by giving that one constant a `{ ... }` body right where it's declared. You declare the method `abstract` in the enum itself (no shared default implementation), and then each constant supplies its own version, exactly like an anonymous subclass. This replaces the need for a big `switch` statement dispatching on which constant you have — each constant simply *is* its own behaviour.

## 2. Why & when

Ordinary enum methods (see [[enums-with-methods]]) share one method body across every constant, differing only in the field values that body reads. But sometimes the *behaviour itself*, not just the data, genuinely differs per constant — think of arithmetic operators (`PLUS` adds, `TIMES` multiplies) or shapes (`CIRCLE` computes area one way, `SQUARE` another). Writing this as a single shared method forces a `switch (this) { case PLUS -> ...; case TIMES -> ...; }` inside the enum — which works, but the compiler cannot verify every constant handled a new case is added later without touching that switch, and the operator-specific logic is visually tangled together in one big method.

Constant-specific method bodies solve this the object-oriented way: each constant becomes responsible for its own implementation, declared right next to where the constant itself is defined. Reach for this whenever different constants need genuinely different *logic* (not just different data plugged into the same logic), and especially when you want the compiler to force every future constant to supply its own implementation — forgetting to override an abstract method on a new constant is a compile error, not a silent runtime gap.

## 3. Core concept

```java
public class OperatorDemo {
    enum Operator {
        PLUS {
            @Override
            int apply(int a, int b) { return a + b; } // this constant's own body
        },
        TIMES {
            @Override
            int apply(int a, int b) { return a * b; } // a different body, same method signature
        };

        abstract int apply(int a, int b); // no shared default -- every constant MUST override
    }

    public static void main(String[] args) {
        System.out.println(Operator.PLUS.apply(3, 4));
        System.out.println(Operator.TIMES.apply(3, 4));
    }
}
```

**How to run:** `java OperatorDemo.java`

`apply` is declared `abstract` inside `Operator`, so the enum itself supplies no shared implementation. Each constant, `PLUS` and `TIMES`, provides its own `{ ... }` body implementing `apply` differently. Calling `.apply()` on each constant dispatches to that specific constant's own code — `PLUS.apply(3, 4)` returns `7`, `TIMES.apply(3, 4)` returns `12`.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="each constant with a curly-brace body is really an anonymous subclass overriding the abstract method with its own distinct implementation">
  <rect x="8" y="8" width="624" height="154" rx="8" fill="#0d1117"/>
  <rect x="30" y="30" width="580" height="30" rx="6" fill="#1c2430" stroke="#f85149"/>
  <text x="320" y="50" fill="#f85149" font-size="11" text-anchor="middle">abstract int apply(int a, int b);  -- no shared body</text>

  <rect x="80" y="80" width="200" height="60" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="180" y="103" fill="#6db33f" font-size="11" text-anchor="middle">PLUS { apply = a + b }</text>
  <text x="180" y="122" fill="#8b949e" font-size="9" text-anchor="middle">anonymous subclass of Operator</text>

  <rect x="360" y="80" width="200" height="60" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="460" y="103" fill="#6db33f" font-size="11" text-anchor="middle">TIMES { apply = a * b }</text>
  <text x="460" y="122" fill="#8b949e" font-size="9" text-anchor="middle">anonymous subclass of Operator</text>
</svg>

Each constant with a body compiles to its own hidden subclass of the enum, overriding the abstract method — dispatch happens through ordinary polymorphism, not a `switch`.

## 5. Runnable example

Scenario: a calculator's operators, evolved from a single shared method using an internal `switch`, through constant-specific bodies removing the switch entirely, to a version where adding a new operator with a guarded body (division by zero) is forced to be handled by the compiler itself.

### Level 1 — Basic

```java
public class OperatorSwitchVersion {
    enum Operator { PLUS, MINUS, TIMES }

    static int apply(Operator op, int a, int b) {
        return switch (op) { // one method, dispatching internally
            case PLUS -> a + b;
            case MINUS -> a - b;
            case TIMES -> a * b;
        };
    }

    public static void main(String[] args) {
        System.out.println(apply(Operator.PLUS, 10, 3));
        System.out.println(apply(Operator.TIMES, 10, 3));
    }
}
```

**How to run:** `java OperatorSwitchVersion.java`

This works and the exhaustive `switch` even catches a missing case at compile time — but the logic for every operator is crammed into one external method, and the operator's own type doesn't carry its behaviour at all.

### Level 2 — Intermediate

```java
public class OperatorConstantBodies {
    enum Operator {
        PLUS { @Override int apply(int a, int b) { return a + b; } },
        MINUS { @Override int apply(int a, int b) { return a - b; } },
        TIMES { @Override int apply(int a, int b) { return a * b; } };

        abstract int apply(int a, int b); // forces every constant to implement its own logic
    }

    public static void main(String[] args) {
        for (Operator op : Operator.values()) {
            System.out.println(op + "(10, 3) = " + op.apply(10, 3));
        }
    }
}
```

**How to run:** `java OperatorConstantBodies.java`

Each operator now owns its own behaviour directly — `Operator.PLUS.apply(10, 3)` doesn't need a `switch` anywhere; ordinary polymorphic dispatch (each constant is really its own tiny subclass) picks the right code automatically.

### Level 3 — Advanced

```java
public class OperatorDivideSafe {
    enum Operator {
        PLUS { @Override int apply(int a, int b) { return a + b; } },
        MINUS { @Override int apply(int a, int b) { return a - b; } },
        TIMES { @Override int apply(int a, int b) { return a * b; } },
        DIVIDE {
            @Override
            int apply(int a, int b) {
                if (b == 0) throw new ArithmeticException("Division by zero in DIVIDE");
                return a / b;
            }
        };

        abstract int apply(int a, int b); // adding DIVIDE forces this override -- compile error if omitted
    }

    static void safeApply(Operator op, int a, int b) {
        try {
            System.out.println(op + "(" + a + ", " + b + ") = " + op.apply(a, b));
        } catch (ArithmeticException e) {
            System.out.println(op + "(" + a + ", " + b + ") failed: " + e.getMessage());
        }
    }

    public static void main(String[] args) {
        safeApply(Operator.DIVIDE, 10, 2);
        safeApply(Operator.DIVIDE, 10, 0);
    }
}
```

**How to run:** `java OperatorDivideSafe.java`

Adding `DIVIDE` demonstrates the real payoff: the compiler forces `DIVIDE` to supply an `apply` body (omitting it is a compile error, since `apply` is `abstract`), and that body can contain operator-specific guard logic — here, rejecting division by zero with a clear exception — entirely local to `DIVIDE`, without touching `PLUS`, `MINUS`, or `TIMES` at all.

## 6. Walkthrough

Execution starts in `main`. `safeApply(Operator.DIVIDE, 10, 2)` runs first: inside its `try` block, `op.apply(a, b)` is called on `DIVIDE` with `a=10, b=2`. This dispatches to `DIVIDE`'s own overridden `apply` — the anonymous subclass generated for the `DIVIDE` constant. Inside, `b == 0` is `2 == 0`, false, so it skips the throw and returns `10 / 2 = 5`. Back in `safeApply`, this is printed as `DIVIDE(10, 2) = 5`.

`safeApply(Operator.DIVIDE, 10, 0)` runs next: `op.apply(10, 0)` again dispatches to `DIVIDE`'s body. This time `b == 0` is `0 == 0`, true, so it throws `new ArithmeticException("Division by zero in DIVIDE")` immediately, before ever reaching the actual division. This exception propagates up out of `apply`, out of the expression inside `safeApply`'s `try` block, and is caught by the `catch (ArithmeticException e)` block, which prints `DIVIDE(10, 0) failed: Division by zero in DIVIDE`.

Notice that `PLUS`, `MINUS`, and `TIMES` never needed any zero-check logic at all — because each constant's body is independent, adding a guard to `DIVIDE` required touching only `DIVIDE`'s own code.

Expected output:
```
DIVIDE(10, 2) = 5
DIVIDE(10, 0) failed: Division by zero in DIVIDE
```

## 7. Gotchas & takeaways

> If even one constant needs a body (`{ ... }`) to override an abstract method, every constant in that enum must supply one — you cannot leave some constants using a "default" and others overriding, unless you also give the abstract method a genuine shared default implementation instead of declaring it `abstract`.

- Give a constant its own behaviour by declaring the enum's method `abstract` and supplying a `{ ... }` body after that constant's name — this is functionally an anonymous subclass of the enum for that one constant.
- This replaces an internal `switch (this) { ... }` with real polymorphic dispatch: calling the method on a constant runs exactly that constant's code, no branching needed.
- The compiler enforces that every constant overrides the abstract method — forgetting one is a compile error, catching a real omission far earlier than a missing `switch` case would (which is only caught if the switch happens to be exhaustive-checked).
- Reach for constant-specific bodies when different constants need genuinely different *logic*; reach for a shared method reading per-constant fields (see [[enums-with-methods]]) when they need the same logic applied to different data.
- Guard logic specific to one constant (like `DIVIDE`'s zero-check) stays fully local to that constant's own body — other constants are never at risk of being affected by, or needing to know about, that guard.
