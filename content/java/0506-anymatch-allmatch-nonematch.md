---
card: java
gi: 506
slug: anymatch-allmatch-nonematch
title: anyMatch / allMatch / noneMatch
---

## 1. What it is

`anyMatch(predicate)`, `allMatch(predicate)`, and `noneMatch(predicate)` are terminal operations that test a stream against a condition and return a `boolean`. `anyMatch` returns `true` if *at least one* element satisfies the predicate. `allMatch` returns `true` if *every* element satisfies it (vacuously `true` for an empty stream). `noneMatch` returns `true` if *no* element satisfies it (also vacuously `true` for an empty stream). All three are **short-circuiting**: they stop scanning as soon as the answer is determined, without necessarily visiting every element.

## 2. Why & when

These three methods answer yes/no questions about a stream's contents without needing to collect or count anything — "does any order exceed the budget?", "are all fields valid?", "does no user have an expired session?" They're more direct than filtering and checking `.count() > 0` or `.count() == totalSize`, and — because they short-circuit — they can be significantly faster, stopping the moment the answer is known rather than always processing every element.

## 3. Core concept

```java
import java.util.stream.*;

List<Integer> scores = List.of(85, 92, 78, 95);

boolean anyFailing = scores.stream().anyMatch(s -> s < 60);   // false -- none below 60
boolean allPassing = scores.stream().allMatch(s -> s >= 70);  // true -- every score is 70+
boolean noneNegative = scores.stream().noneMatch(s -> s < 0); // true -- no negative scores
```

Each method answers a specific yes/no question about the whole stream, stopping early the moment the outcome is certain — `anyMatch` stops at the first match, `allMatch`/`noneMatch` stop at the first counterexample.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="anyMatch stops at the first match; allMatch and noneMatch stop at the first counterexample">
  <rect x="8" y="8" width="624" height="134" rx="8" fill="#0d1117"/>
  <text x="20" y="30" fill="#8b949e" font-size="11" font-family="sans-serif">anyMatch(s -&gt; s &lt; 60):</text>
  <rect x="220" y="15" width="45" height="28" fill="#1c2430" stroke="#6db33f"/><text x="242" y="34" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace">85</text>
  <rect x="270" y="15" width="45" height="28" fill="#1c2430" stroke="#6db33f"/><text x="292" y="34" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace">92</text>
  <rect x="320" y="15" width="45" height="28" fill="#0d1117" stroke="#8b949e" stroke-dasharray="3,2"/><text x="342" y="34" fill="#8b949e" font-size="11" text-anchor="middle" font-family="monospace">78</text>
  <text x="400" y="34" fill="#8b949e" font-size="10" font-family="sans-serif">(stops once match found)</text>

  <text x="20" y="80" fill="#8b949e" font-size="11" font-family="sans-serif">allMatch(s -&gt; s &gt;= 70):</text>
  <rect x="220" y="65" width="45" height="28" fill="#1c2430" stroke="#6db33f"/><text x="242" y="84" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace">85</text>
  <rect x="270" y="65" width="45" height="28" fill="#1c2430" stroke="#6db33f"/><text x="292" y="84" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace">92</text>
  <rect x="320" y="65" width="45" height="28" fill="#1c2430" stroke="#6db33f"/><text x="342" y="84" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace">78</text>
  <rect x="370" y="65" width="45" height="28" fill="#1c2430" stroke="#6db33f"/><text x="392" y="84" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace">95</text>
  <text x="450" y="84" fill="#8b949e" font-size="10" font-family="sans-serif">(all checked -- all pass)</text>
  <text x="20" y="130" fill="#8b949e" font-size="10" font-family="sans-serif">anyMatch stops early on a hit; allMatch/noneMatch stop early only on a miss/counterexample.</text>
</svg>

`anyMatch` can stop as soon as it finds a match; `allMatch`/`noneMatch` must check every element unless they hit a disqualifying counterexample first.

## 5. Runnable example

Scenario: validating a batch of form submissions before processing — evolved from a single-condition check, through combining multiple validation rules, to a version that reports specifically *which* rule failed rather than just a pass/fail boolean.

### Level 1 — Basic

```java
import java.util.*;
import java.util.stream.*;

public class MatchBasic {
    record Submission(String email, int age) {}

    public static void main(String[] args) {
        List<Submission> submissions = List.of(
                new Submission("alice@example.com", 25),
                new Submission("bob@example.com", 17),
                new Submission("carol@example.com", 30)
        );

        boolean anyMinor = submissions.stream().anyMatch(s -> s.age() < 18);
        System.out.println("Any minors? " + anyMinor);
    }
}
```

**How to run:** `java MatchBasic.java`

Expected output:
```
Any minors? true
```

`.anyMatch(s -> s.age() < 18)` scans the submissions looking for at least one match. `Bob` (age `17`) satisfies the predicate, so `anyMatch` returns `true` — and, being short-circuiting, it would have stopped scanning the moment it found `Bob`, without necessarily checking `Carol` afterward (order of evaluation follows the stream's encounter order for a sequential stream).

### Level 2 — Intermediate

```java
import java.util.*;
import java.util.stream.*;

public class MatchCombined {
    record Submission(String email, int age) {}

    public static void main(String[] args) {
        List<Submission> submissions = List.of(
                new Submission("alice@example.com", 25),
                new Submission("bob@example.com", 22),
                new Submission("carol@example.com", 30)
        );

        boolean allAdults = submissions.stream().allMatch(s -> s.age() >= 18);
        boolean allHaveValidEmail = submissions.stream().allMatch(s -> s.email().contains("@"));
        boolean noneBlank = submissions.stream().noneMatch(s -> s.email().isBlank());

        boolean batchValid = allAdults && allHaveValidEmail && noneBlank;
        System.out.println("Batch valid: " + batchValid);
    }
}
```

**How to run:** `java MatchCombined.java`

Expected output:
```
Batch valid: true
```

The real-world concern this adds: real validation usually needs *multiple* independent checks combined together. Here, `allAdults`, `allHaveValidEmail`, and `noneBlank` are each computed with a separate `allMatch`/`noneMatch` call (each re-streaming the source), and combined with `&&` into one overall `batchValid` flag — all three individually returning `true` for this clean data set.

### Level 3 — Advanced

```java
import java.util.*;
import java.util.function.*;
import java.util.stream.*;

public class MatchDiagnostic {
    record Submission(String email, int age) {}
    record Rule(String description, Predicate<Submission> mustHold) {}

    public static void main(String[] args) {
        List<Submission> submissions = List.of(
                new Submission("alice@example.com", 25),
                new Submission("bob", 17), // fails both rules
                new Submission("carol@example.com", 30)
        );

        List<Rule> rules = List.of(
                new Rule("must be an adult", s -> s.age() >= 18),
                new Rule("must have a valid email", s -> s.email().contains("@"))
        );

        // Report exactly which rule fails for which submission, instead of one opaque boolean.
        for (Rule rule : rules) {
            boolean allPass = submissions.stream().allMatch(rule.mustHold());
            if (!allPass) {
                List<String> violators = submissions.stream()
                        .filter(s -> !rule.mustHold().test(s))
                        .map(Submission::email)
                        .toList();
                System.out.println("Rule '" + rule.description() + "' FAILED for: " + violators);
            } else {
                System.out.println("Rule '" + rule.description() + "' passed for all submissions");
            }
        }
    }
}
```

**How to run:** `java MatchDiagnostic.java`

Expected output:
```
Rule 'must be an adult' FAILED for: [bob]
Rule 'must have a valid email' FAILED for: [bob]
```

This turns the pass/fail boolean from `allMatch` into an actionable diagnostic: for each `Rule`, `allMatch(rule.mustHold())` first checks if everyone passes; if not, a second pass with `.filter(...)` (the negation of the same rule) identifies specifically *which* submissions violated it. `bob` (`"bob"`, no `@`, age `17`) fails both rules and is correctly reported both times.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `submissions` holds three entries: `alice` (valid email, age `25`), `bob` (`"bob"` — no `@`, age `17`), `carol` (valid email, age `30`). `rules` defines two `Rule`s: adulthood and valid email.

The `for` loop processes `rules` one at a time. For the first rule, `"must be an adult"` (`s -> s.age() >= 18`): `submissions.stream().allMatch(rule.mustHold())` checks each submission — `alice.age() >= 18` is `25 >= 18`, `true`; `bob.age() >= 18` is `17 >= 18`, `false`. The moment `allMatch` hits this `false` result for `bob`, it can short-circuit and immediately return `false` overall — `carol` may or may not actually be checked depending on internal stream mechanics, but the *result* is determined: `allPass = false`.

Since `allPass` is `false`, a second, separate pass runs: `submissions.stream().filter(s -> !rule.mustHold().test(s))` keeps only submissions where the rule does **not** hold — for `alice`, `!(25 >= 18)` is `!true` = `false` (excluded); for `bob`, `!(17 >= 18)` is `!false` = `true` (kept); for `carol`, `!(30 >= 18)` is `false` (excluded). `.map(Submission::email)` extracts just `bob`'s email, `"bob"`. The line `"Rule 'must be an adult' FAILED for: [bob]"` prints.

The loop then processes the second rule, `"must have a valid email"` (`s -> s.email().contains("@")`): `allMatch` checks `alice.email().contains("@")` true, `bob.email().contains("@")` — `"bob".contains("@")` is `false`, short-circuits to `allPass = false`. The filter pass then identifies `bob` again (his email lacks `@`, while `alice` and `carol`'s do contain it), printing `"Rule 'must have a valid email' FAILED for: [bob]"`.

```
Rule "adult" (age >= 18):
  alice(25): true   bob(17): false <- allMatch short-circuits here, result=false
  filter pass: alice excluded, bob KEPT, carol excluded -> violators=[bob]

Rule "valid email" (contains "@"):
  alice: true   bob: false <- allMatch short-circuits here, result=false
  filter pass: alice excluded, bob KEPT, carol excluded -> violators=[bob]
```

Both rules report `bob` as the sole violator, giving a clear, actionable diagnostic instead of a single opaque `false` — exactly the kind of detail a plain `allMatch` call alone cannot provide on its own.

## 7. Gotchas & takeaways

> `allMatch` and `noneMatch` both return `true` for an **empty** stream — this is "vacuous truth" (there are no elements to violate the condition, so the condition trivially holds for all zero of them). This can be surprising: `List.<Integer>of().stream().allMatch(n -> n > 100)` is `true`, even though intuitively an empty list has no elements greater than `100` to point to. Always consider whether an empty input should really count as passing validation.

- `anyMatch` is `true` if at least one element satisfies the predicate; `allMatch` is `true` if every element does; `noneMatch` is `true` if no element does.
- All three short-circuit: `anyMatch` stops at the first match, `allMatch`/`noneMatch` stop at the first counterexample — none of them necessarily visit every element.
- `allMatch(p)` and `noneMatch(p.negate())` are logically equivalent (and vice versa) — pick whichever reads more naturally for the condition you're expressing.
- Both `allMatch` and `noneMatch` are vacuously `true` on an empty stream — worth double-checking against your intended semantics, especially for validation logic where an empty input might actually be invalid.
- When a plain `boolean` isn't enough — you need to know *which* elements caused a failure — a `filter` pass with the negated predicate (as in Level 3) turns "did it pass?" into "what failed, specifically?"
