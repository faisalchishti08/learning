---
card: java
gi: 1038
slug: semantic-versioning
title: Semantic versioning
---

## 1. What it is

Semantic Versioning (SemVer) is a convention for version numbers in the form `MAJOR.MINOR.PATCH` (e.g. `2.4.1`) where each segment has a precise, agreed-upon meaning: increment **MAJOR** when you make an incompatible ("breaking") API change, increment **MINOR** when you add functionality in a backward-compatible way, and increment **PATCH** when you make backward-compatible bug fixes. The point isn't just organization — it's a **promise**: a consumer of your library can look at a version bump alone and know, without reading a changelog, whether upgrading is safe to do blindly (patch or minor) or requires checking for breaking changes first (major).

## 2. Why & when

Without an agreed convention, a version bump from `1.2.0` to `1.3.0` tells a consumer nothing — it might be a trivial bug fix, or it might silently remove a method they depend on, and the only way to find out is to read the changelog (if one exists) or discover it the hard way when their build breaks. SemVer turns the version number itself into a machine-and-human-readable signal: a dependency-management tool can automatically accept new patch and minor versions (since the promise is they're backward compatible) while flagging major version bumps for manual review, and Maven/Gradle's `[1.0,2.0)` style version ranges rely directly on this convention meaning what it says.

Apply SemVer to any library or API that other code depends on — an internal shared library between teams, a published open-source artifact, a public REST API's versioning scheme. The discipline matters most exactly at the moment you're deciding "is this change breaking or not?" — that judgment call, made honestly, is what makes the whole convention trustworthy for everyone downstream.

## 3. Core concept

```
1.4.2
│ │ └── PATCH: bug fixes, no API changes at all -- always safe to upgrade
│ └──── MINOR: new functionality added, but nothing existing was removed or changed
└────── MAJOR: at least one BREAKING change -- existing callers may need code changes

// Examples of what forces each kind of bump:
// PATCH (1.4.2 -> 1.4.3): fixed a bug where discount() rounded incorrectly
// MINOR (1.4.2 -> 1.5.0): added a new optional overload discount(double, Currency)
// MAJOR (1.4.2 -> 2.0.0): removed the old discount(double) method entirely,
//                          or changed its return type from double to BigDecimal
```

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A version number 1.4.2 broken into MAJOR, MINOR, and PATCH segments, each labeled with what kind of change justifies incrementing it">
  <text x="150" y="40" fill="#e6edf3" font-size="28" text-anchor="middle" font-family="monospace">1</text>
  <text x="150" y="65" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">MAJOR</text>
  <text x="150" y="80" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">breaking changes</text>

  <text x="320" y="40" fill="#e6edf3" font-size="28" text-anchor="middle" font-family="monospace">4</text>
  <text x="320" y="65" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">MINOR</text>
  <text x="320" y="80" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">new, compatible features</text>

  <text x="490" y="40" fill="#e6edf3" font-size="28" text-anchor="middle" font-family="monospace">2</text>
  <text x="490" y="65" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">PATCH</text>
  <text x="490" y="80" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">bug fixes only</text>
</svg>

Each segment of a SemVer version number carries a distinct, promised meaning about what kind of change it represents.

## 5. Runnable example

Scenario: a small `DiscountCalculator` library evolving across three releases, showing exactly which kind of change justifies each version bump.

### Level 1 — Basic

```java
// File: DiscountCalculator.java -- version 1.0.0
public class DiscountCalculator {
    // Bug: rounds down when it should round to the nearest cent.
    public double discount(double price, double percentOff) {
        return Math.floor((price * (1 - percentOff / 100.0)) * 100) / 100;
    }

    public static void main(String[] args) {
        System.out.println("v1.0.0: " + new DiscountCalculator().discount(19.995, 10));
    }
}
```

**How to run:** save as `DiscountCalculator.java`, then `javac DiscountCalculator.java && java DiscountCalculator` (JDK 17+).

Expected output:
```
v1.0.0: 17.99
```

The rounding-down behavior for `19.995 * 0.90 = 17.9955` produces `17.99`, but the more correct rounding is `18.0` — this is a genuine bug, and fixing it changes no public method signature at all.

### Level 2 — Intermediate

```java
// File: DiscountCalculator.java -- version 1.0.1 (PATCH: bug fix, no API change)
public class DiscountCalculator {
    // Fixed: rounds to the nearest cent instead of always flooring.
    public double discount(double price, double percentOff) {
        return Math.round((price * (1 - percentOff / 100.0)) * 100) / 100.0;
    }

    public static void main(String[] args) {
        System.out.println("v1.0.1: " + new DiscountCalculator().discount(19.995, 10));
    }
}
```

**How to run:** save as `DiscountCalculator.java`, then `javac DiscountCalculator.java && java DiscountCalculator` (JDK 17+).

Expected output:
```
v1.0.1: 18.0
```

The real-world concern added: the bug is fixed with `Math.round` instead of `Math.floor`, but the method's name, parameter types, and return type are all completely unchanged — any existing caller of `discount(double, double)` keeps compiling and working exactly as before, just with more correct results. This qualifies as a **PATCH** bump: `1.0.0` → `1.0.1`.

### Level 3 — Advanced

```java
// File: DiscountCalculator.java -- version 1.1.0 (MINOR: new capability added, nothing removed)
import java.math.BigDecimal;
import java.math.RoundingMode;

public class DiscountCalculator {
    // Unchanged from 1.0.1 -- existing callers of THIS method are completely unaffected.
    public double discount(double price, double percentOff) {
        return Math.round((price * (1 - percentOff / 100.0)) * 100) / 100.0;
    }

    // NEW overload added -- a genuinely new capability (BigDecimal precision for
    // financial calculations), but nothing existing was changed or removed.
    public BigDecimal discount(BigDecimal price, BigDecimal percentOff) {
        BigDecimal multiplier = BigDecimal.ONE.subtract(
            percentOff.divide(BigDecimal.valueOf(100), 10, RoundingMode.HALF_UP));
        return price.multiply(multiplier).setScale(2, RoundingMode.HALF_UP);
    }

    public static void main(String[] args) {
        DiscountCalculator calc = new DiscountCalculator();
        System.out.println("v1.1.0 double: " + calc.discount(19.995, 10));
        System.out.println("v1.1.0 BigDecimal: " + calc.discount(new BigDecimal("19.995"), new BigDecimal("10")));
    }
}
```

**How to run:** save as `DiscountCalculator.java`, then `javac DiscountCalculator.java && java DiscountCalculator` (JDK 17+).

Expected output:
```
v1.1.0 double: 18.0
v1.1.0 BigDecimal: 18.00
```

The production-flavored hard case: the original `discount(double, double)` method still exists, unchanged, working exactly as it did in `1.0.1` — every existing caller keeps compiling with zero code changes required. The new `discount(BigDecimal, BigDecimal)` overload is purely additive. This qualifies as a **MINOR** bump: `1.0.1` → `1.1.0` — not a major bump, since nothing existing broke or was removed, and not a patch, since genuinely new functionality was added.

## 6. Walkthrough

Tracing why each transition above earns its specific SemVer bump, and what a hypothetical fourth change would require:

1. `1.0.0` → `1.0.1`: the only change was *inside* `discount(double, double)`'s implementation (`Math.floor` became `Math.round`) — the method's signature (name, parameter types, return type) is byte-for-byte identical, so any code compiled against `1.0.0` continues to compile and link against `1.0.1` without modification. This is exactly what PATCH promises: a pure bug fix, safe to adopt without reviewing anything.
2. `1.0.1` → `1.1.0`: a brand-new public method, `discount(BigDecimal, BigDecimal)`, was added — but `discount(double, double)` remains present with its exact prior signature and behavior. Existing code compiled against `1.0.1` still compiles and runs identically against `1.1.0`; only code that wants to *use* the new overload needs to be written. This is exactly what MINOR promises: new capability, zero risk to existing callers.
3. Now consider a hypothetical fourth release that removes `discount(double, double)` entirely, keeping only the `BigDecimal` overload, reasoning that "everyone should use the more precise version now." Any code still calling `discount(double, double)` would fail to *compile* against this new version — that's an incompatible, breaking change.
4. Per SemVer's rule, this hypothetical release **must** be `2.0.0`, not `1.2.0` — bumping MAJOR is the signal that tells every consumer "check for breaking changes before upgrading," rather than the false reassurance a MINOR or PATCH bump would give.
5. This is precisely the value of the discipline: a consumer of this library, seeing a jump from `1.x` to `2.0.0` in a dependency-management tool's update suggestion, knows *without reading a single line of the changelog* that upgrading requires actually checking their code for compatibility — whereas a `1.0.1` → `1.1.0` or `1.1.0` → `1.1.1` bump can be adopted with much higher confidence that nothing will break.
6. This is also exactly what makes Maven/Gradle version ranges like `[1.0,2.0)` (meaning "any 1.x version, but never 2.0 or above") meaningful and trustworthy — the range only makes sense as a safety boundary if MAJOR version bumps are reserved, honestly and consistently, for genuinely breaking changes.

## 7. Gotchas & takeaways

> **Gotcha:** SemVer is a promise enforced by discipline, not by the compiler or any tool — nothing stops a library maintainer from sneaking a breaking change into a MINOR or PATCH release by mistake (or carelessness), and when that happens, every consumer who trusted the convention and auto-upgraded gets a broken build with no warning. The convention's value depends entirely on maintainers honoring it correctly.

- SemVer's `MAJOR.MINOR.PATCH` format is a promise: PATCH means bug fixes only, MINOR means new backward-compatible functionality, MAJOR means at least one breaking change.
- The critical judgment call is deciding whether a given change is genuinely backward-compatible — removing a public method, changing a method's return type, or changing its thrown-exception contract are all breaking changes requiring a MAJOR bump.
- Adding a new overload, a new optional parameter (via a new overload, since Java doesn't have optional parameters), or a new public class is typically backward-compatible and qualifies as MINOR.
- Dependency-management tooling (version ranges, automated update bots) relies on SemVer being honored accurately — a careless breaking change hidden in a MINOR release undermines the trust the whole ecosystem places in the convention.
- See [dependency management & conflicts](1039-dependency-management-conflicts.md) for how version numbers (and the SemVer promise behind them) get used when Maven or Gradle has to resolve which version of a shared transitive dependency to actually use.
- Don't treat SemVer as purely mechanical — a change that's technically source-compatible but behaviorally different in a way that could break a caller relying on the old behavior (a bug fix that callers had started depending on) is a genuinely hard judgment call, not something a tool can decide for you.
