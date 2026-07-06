---
card: java
gi: 228
slug: final-methods-prevent-override
title: Final methods (prevent override)
---

## 1. What it is

This topic focuses specifically on `final`'s effect on **methods**, building on the general `final` overview from earlier: a `final` method cannot be overridden by any subclass, ever. Attempting to declare a method in a subclass with the exact same signature as an inherited `final` method is a compile error — the compiler catches this immediately, guaranteeing that a `final` method's behaviour, once defined, can never be altered anywhere down the entire inheritance hierarchy.

```java
class Account {
    private double balance;

    final void deposit(double amount) { // final: NO subclass can ever override this
        if (amount <= 0) throw new IllegalArgumentException("Deposit must be positive");
        balance += amount;
    }

    double getBalance() { return balance; }
}

class SavingsAccount extends Account {
    // void deposit(double amount) { ... } // COMPILE ERROR if uncommented — cannot override a final method
}
```

`Account.deposit` is `final`, so `SavingsAccount` (or any other subclass, at any depth) is structurally prevented from overriding it — this guarantees that *every* deposit into *any* kind of `Account`, regardless of subclass, always goes through exactly this one validated implementation, with no possibility of a subclass silently bypassing or weakening that validation.

## 2. Why & when

Marking a method `final` is a deliberate design decision to lock in behaviour that the class's correctness genuinely depends on staying consistent across every subclass:

- **Protecting critical invariants** — if a method's exact behaviour (like validating a deposit amount before applying it) is essential to the class working correctly, allowing a subclass to override it could silently undermine that guarantee, potentially introducing bugs or security issues far from where the original class was defined.
- **Performance** — since a `final` method can never be overridden, the JVM can sometimes resolve calls to it more efficiently (using static binding, as covered in the previous topic), skipping the dynamic dispatch lookup that ordinary overridable methods require, though this optimization is a secondary benefit, not the primary reason to reach for `final`.
- **Communicating design intent clearly** — marking a method `final` tells every future maintainer (including future you) explicitly: "this behaviour is not meant to be customized by subclasses," which is valuable documentation enforced directly by the compiler, not just a comment that could be ignored.

You mark a method `final` specifically when allowing an override would risk breaking something the class relies on for correctness — template methods that call other overridable methods in a fixed, essential sequence (a pattern in more advanced object-oriented design) are a particularly common place `final` shows up, precisely to lock down that sequence while still allowing customization of the individual steps.

## 3. Core concept

```java
class Recipe {
    final void cook() { // final: the OVERALL sequence can never be changed by a subclass
        prepareIngredients();
        applyHeat();
        plate();
    }

    void prepareIngredients() { System.out.println("Generic prep"); }
    void applyHeat() { System.out.println("Generic heating"); }
    void plate() { System.out.println("Generic plating"); }
}

class PastaRecipe extends Recipe {
    @Override
    void prepareIngredients() { System.out.println("Boiling water for pasta"); } // customizable step

    @Override
    void applyHeat() { System.out.println("Simmering sauce"); } // customizable step

    // cook() itself cannot be overridden — the sequence is locked
}
```

`cook()` is `final`, locking the *order* of the three steps permanently, while `prepareIngredients()`, `applyHeat()`, and `plate()` remain ordinary, overridable methods — this combination (a `final` "template" method calling overridable "step" methods) is a deliberate, common design pattern that locks down structure while still allowing meaningful customization.

## 4. Diagram

<svg viewBox="0 0 600 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A final cook method locking a fixed three step sequence of prepare heat and plate, where each individual step remains an overridable method a subclass can customize, but the overall sequence and order can never be changed by any subclass">
  <rect x="8" y="8" width="584" height="154" rx="8" fill="#0d1117"/>

  <rect x="180" y="20" width="240" height="35" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="2"/>
  <text x="300" y="42" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">final void cook() — LOCKED sequence</text>

  <line x1="300" y1="55" x2="300" y2="70" stroke="#8b949e" stroke-width="1.5"/>

  <rect x="60" y="75" width="140" height="35" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="130" y="97" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">prepareIngredients()</text>

  <rect x="230" y="75" width="140" height="35" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="300" y="97" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">applyHeat()</text>

  <rect x="400" y="75" width="140" height="35" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="470" y="97" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">plate()</text>

  <text x="300" y="135" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Each step (blue) is overridable and customizable.</text>
  <text x="300" y="153" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">The overall sequence and order (red) can never be changed by any subclass.</text>
</svg>

A `final` template method locks the sequence; the individual overridable steps within it remain customizable.

## 5. Runnable example

Scenario: a small authentication system where the core validation sequence must never be bypassed by a subclass — starting with a basic final method preventing an override attempt, then extending with a template-method pattern combining a final sequence with customizable steps, then hardening into a case demonstrating exactly why this guarantee matters for security-sensitive logic.

### Level 1 — Basic

```java
public class FinalMethodBasic {
    static class Authenticator {
        final boolean login(String username, String password) { // final: cannot be weakened by a subclass
            if (username == null || password == null) {
                return false;
            }
            return password.length() >= 8; // simplified check, for illustration
        }
    }

    static class AdminAuthenticator extends Authenticator {
        // boolean login(String u, String p) { return true; } // COMPILE ERROR if uncommented
    }

    public static void main(String[] args) {
        AdminAuthenticator auth = new AdminAuthenticator();
        System.out.println(auth.login("admin", "short"));       // false — inherited validation still applies
        System.out.println(auth.login("admin", "longenough")); // true
    }
}
```

**How to run:** `java FinalMethodBasic.java`

`AdminAuthenticator` inherits `login` unchanged, since it's `final` and cannot be overridden — even a subclass explicitly named `AdminAuthenticator` (which might tempt someone to weaken the check "just for admins") is structurally prevented from bypassing this validation.

### Level 2 — Intermediate

Same authentication idea, now using the template-method pattern: a `final` method defining a fixed validation sequence, calling overridable steps that subclasses *can* customize.

```java
public class FinalMethodIntermediate {
    static class Authenticator {
        final boolean login(String username, String password) { // final: sequence locked
            if (!isValidUsername(username)) return false;
            if (!isValidPassword(password)) return false;
            return true;
        }

        boolean isValidUsername(String username) { // overridable step
            return username != null && !username.isEmpty();
        }

        boolean isValidPassword(String password) { // overridable step
            return password != null && password.length() >= 8;
        }
    }

    static class StrictAuthenticator extends Authenticator {
        @Override
        boolean isValidPassword(String password) { // customizes just this one step
            return password != null && password.length() >= 12; // stricter requirement
        }
    }

    public static void main(String[] args) {
        Authenticator basic = new Authenticator();
        Authenticator strict = new StrictAuthenticator();

        System.out.println(basic.login("user", "eightchr"));   // true — meets basic's 8-char rule
        System.out.println(strict.login("user", "eightchr"));  // false — fails strict's 12-char rule
    }
}
```

**How to run:** `java FinalMethodIntermediate.java`

`StrictAuthenticator` customizes only `isValidPassword`, while `login`'s overall sequence (check username, then check password) remains fixed and identical for both — the `final` method guarantees the *structure* of validation can never be reordered or skipped, while individual steps remain flexibly customizable.

### Level 3 — Advanced

Same authentication system, now demonstrating concretely why locking the sequence matters: without `final`, a malicious or careless subclass override of the whole `login` method could bypass validation entirely — something the `final` keyword makes structurally impossible.

```java
public class FinalMethodAdvanced {
    // Demonstrates the RISK (hypothetically) if login() were NOT final — shown via a separate, non-final version
    static class UnsafeAuthenticator {
        boolean login(String username, String password) { // NOT final — can be overridden entirely
            if (!isValidUsername(username)) return false;
            if (!isValidPassword(password)) return false;
            return true;
        }
        boolean isValidUsername(String username) { return username != null && !username.isEmpty(); }
        boolean isValidPassword(String password) { return password != null && password.length() >= 8; }
    }

    static class BackdoorAuthenticator extends UnsafeAuthenticator {
        @Override
        boolean login(String username, String password) { // completely REPLACES the validation sequence!
            return true; // always succeeds, bypassing every check entirely
        }
    }

    // The SAFE version, using final to prevent exactly this risk
    static class SafeAuthenticator {
        final boolean login(String username, String password) {
            if (!isValidUsername(username)) return false;
            if (!isValidPassword(password)) return false;
            return true;
        }
        boolean isValidUsername(String username) { return username != null && !username.isEmpty(); }
        boolean isValidPassword(String password) { return password != null && password.length() >= 8; }
    }

    public static void main(String[] args) {
        UnsafeAuthenticator backdoor = new BackdoorAuthenticator();
        System.out.println("Backdoor login with garbage credentials: " + backdoor.login(null, "x")); // true! validation bypassed

        SafeAuthenticator safe = new SafeAuthenticator();
        System.out.println("Safe login with garbage credentials: " + safe.login(null, "x")); // false — final protects this
    }
}
```

**How to run:** `java FinalMethodAdvanced.java`

`BackdoorAuthenticator` completely overrides `login` (legal only because `UnsafeAuthenticator.login` is *not* `final`), discarding all validation and always returning `true` — a serious security hole; `SafeAuthenticator.login`, being `final`, makes this exact kind of override structurally impossible to write in the first place, guaranteeing the validation sequence always runs for every subclass.

## 6. Walkthrough

Trace both login calls in `FinalMethodAdvanced.main`, both using clearly invalid credentials (`null` username, `"x"` as a too-short password):

**`backdoor.login(null, "x")`.** `backdoor`'s actual type is `BackdoorAuthenticator`, which **completely overrides** `login` — dynamic dispatch runs `BackdoorAuthenticator.login`, whose entire body is simply `return true;`, with no validation logic executed at all. The result is `true`, despite the credentials being obviously invalid — this is the security hole.

**`safe.login(null, "x")`.** `safe`'s type is `SafeAuthenticator`, whose `login` is `final` — no subclass exists here to override it anyway, but even if one were attempted, it would fail to compile. `isValidUsername(null)` checks `null != null` — false — so `isValidUsername` returns `false` immediately. Back in `login`, `!isValidUsername(username)` is `!false = true`, so the guard fires: `return false;` — the method exits immediately, without even checking the password.

```
BackdoorAuthenticator.login(null, "x"):
  entire validation sequence REPLACED by the override -> always returns true (BYPASSED)

SafeAuthenticator.login(null, "x"):
  isValidUsername(null) -> null != null? false -> returns false
  !isValidUsername(...) -> true -> guard fires -> return false immediately
```

**Final output.** `"Backdoor login with garbage credentials: true"` (the security hole made possible by the *absence* of `final`) followed by `"Safe login with garbage credentials: false"` (the correct, safe result, guaranteed by `final` making the entire override that caused the backdoor structurally impossible to write).

## 7. Gotchas & takeaways

> **`final` only prevents *overriding* the method itself — it does not prevent a subclass from adding entirely new, unrelated methods, nor does it prevent the class from being extended at all** (that would require the *class* itself to be `final`, a separate, broader guarantee covered in the general `final` topic). A `final` method coexists perfectly well within an otherwise fully extensible class.

> **The template-method pattern (a `final` method orchestrating calls to overridable "step" methods) is a deliberate, common design technique** — it locks down the parts of a class's behaviour that must stay consistent (the sequence, the validation gates) while still allowing genuine, safe customization of the individual steps a subclass is meant to specialize.

- A `final` method cannot be overridden by any subclass, at any depth in the hierarchy — the compiler enforces this immediately.
- Mark a method `final` specifically when a subclass overriding it could break an invariant or guarantee the class depends on.
- The template-method pattern combines a `final` method (locking a critical sequence) with overridable step methods (allowing safe customization).
- `final` on a method only prevents overriding that specific method — it says nothing about the class's overall extensibility, which is governed separately by whether the class itself is `final`.
