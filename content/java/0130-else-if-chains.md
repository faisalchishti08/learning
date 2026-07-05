---
card: java
gi: 130
slug: else-if-chains
title: else-if chains
---

## 1. What it is

An `else if` chain extends `if`/`else` to handle more than two mutually exclusive alternatives: `if (cond1) {...} else if (cond2) {...} else if (cond3) {...} else {...}`. There is no separate `else if` keyword in Java's grammar — it is simply an `if` statement used as the (single) statement inside an `else` clause, which is why the indentation convention keeps each `else if` at the same level rather than nesting deeper and deeper. Conditions are checked **in order**, top to bottom, and execution stops at the *first* one that evaluates to `true` — every subsequent condition in the chain is never even evaluated.

```java
int score = 82;
if (score >= 90) {
    System.out.println("A");
} else if (score >= 80) {
    System.out.println("B");     // this one matches and runs
} else if (score >= 70) {
    System.out.println("C");      // never even checked, because the previous branch already matched
} else {
    System.out.println("F");
}
```

Because evaluation stops at the first match, **order matters** — conditions must be arranged so that more specific or higher-priority cases come before more general ones, or a broad early condition can accidentally "shadow" a later, more specific one that would otherwise have applied.

## 2. Why & when

`else if` chains are the natural tool whenever a value needs to be classified into one of several (more than two) mutually exclusive categories:

- Grading tiers, as above: mapping a numeric score into a letter grade based on threshold ranges.
- HTTP status handling: `if (status < 300) {...} else if (status < 400) {...} else if (status < 500) {...} else {...}` for success/redirect/client-error/server-error categories.
- Simple rule-based dispatch when the number of cases is small and stable; a `switch` (covered separately) often becomes preferable once the number of discrete cases grows large or the branching is on a single value's exact identity rather than a range/complex condition.

## 3. Core concept

```java
public class ElseIfDemo {
    public static void main(String[] args) {
        int[] scores = { 95, 82, 71, 55 };

        for (int score : scores) {
            String grade;
            if (score >= 90) {
                grade = "A";
            } else if (score >= 80) {
                grade = "B";
            } else if (score >= 70) {
                grade = "C";
            } else if (score >= 60) {
                grade = "D";
            } else {
                grade = "F";
            }
            System.out.println("Score " + score + " -> Grade " + grade);
        }

        // Order matters: a broad condition placed too early "shadows" later, more specific ones
        int status = 404;
        if (status >= 200) {          // BUG: this matches almost everything, including 404!
            System.out.println("Treated as success (WRONG)");
        } else if (status >= 400) {
            System.out.println("Client error (never reached for status=404)");
        }
    }
}
```

## 4. Diagram

<svg viewBox="0 0 700 175" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="else if chain diagram: conditions are checked top to bottom in sequence, and execution stops at the first true condition, running only that branch. All conditions below the matching one are never evaluated at all.">
  <rect x="8" y="8" width="684" height="159" rx="8" fill="#0d1117"/>
  <text x="350" y="24" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">score = 82 — checked top to bottom, stops at the FIRST match</text>

  <rect x="20" y="34" width="200" height="26" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="120" y="51" fill="#79c0ff" font-size="8.5" text-anchor="middle" font-family="monospace">score &gt;= 90?  FALSE</text>

  <rect x="20" y="64" width="200" height="26" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="120" y="81" fill="#6db33f" font-size="8.5" text-anchor="middle" font-family="monospace">score &gt;= 80?  TRUE ✓</text>

  <rect x="20" y="94" width="200" height="26" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1" stroke-dasharray="3,2"/>
  <text x="120" y="111" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="monospace">score &gt;= 70?  SKIPPED</text>

  <rect x="20" y="124" width="200" height="26" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1" stroke-dasharray="3,2"/>
  <text x="120" y="141" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="monospace">score &gt;= 60?  SKIPPED</text>

  <rect x="280" y="70" width="180" height="34" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="370" y="92" fill="#6db33f" font-size="10" text-anchor="middle" font-family="monospace">grade = "B" runs</text>
  <path d="M 220 77 L 280 87" stroke="#6db33f" stroke-width="2"/>

  <text x="500" y="90" fill="#8b949e" font-size="8.5" font-family="sans-serif">Once matched, every</text>
  <text x="500" y="104" fill="#8b949e" font-size="8.5" font-family="sans-serif">later condition is</text>
  <text x="500" y="118" fill="#8b949e" font-size="8.5" font-family="sans-serif">never evaluated at all.</text>
</svg>

Only the first matching condition's branch runs; every condition after it — even ones that would also be `true` — is never checked.

## 5. Runnable example

Scenario: an HTTP-response classifier that categorizes status codes — starting with a naive, incorrectly ordered chain that silently misclassifies real errors as successes, then fixed by reordering from most-specific to least-specific.

### Level 1 — Basic

```java
public class HttpBasic {
    public static void main(String[] args) {
        int[] statusCodes = { 200, 301, 404, 500 };

        for (int status : statusCodes) {
            String category;
            // BUG: checking the broadest condition FIRST shadows every later, narrower one
            if (status >= 200) {
                category = "Success";
            } else if (status >= 300) {
                category = "Redirect";
            } else if (status >= 400) {
                category = "Client Error";
            } else if (status >= 500) {
                category = "Server Error";
            } else {
                category = "Unknown";
            }
            System.out.println(status + " -> " + category);
        }
    }
}
```

**How to run:** `java HttpBasic.java`

Every single status code in this example prints `"Success"`, even `404` and `500` — because `status >= 200` is `true` for all of them (`301 >= 200`, `404 >= 200`, and `500 >= 200` are all `true`), and since it's the *first* condition checked, it matches immediately and every subsequent, more specific `else if` is never even evaluated. This is a direct consequence of `else if` chains stopping at the first match: the broadest condition was placed first, so it "shadows" every narrower condition that should have taken precedence for higher status codes.

### Level 2 — Intermediate

Same classifier, now correctly ordered from most restrictive (narrowest range) to least restrictive (broadest range), which is the general rule for range-based `else if` chains: check the most specific/highest-priority condition first.

```java
public class HttpIntermediate {
    public static void main(String[] args) {
        int[] statusCodes = { 200, 301, 404, 500 };

        for (int status : statusCodes) {
            String category;
            // Fixed: check narrower, more specific ranges FIRST
            if (status >= 500) {
                category = "Server Error";
            } else if (status >= 400) {
                category = "Client Error";
            } else if (status >= 300) {
                category = "Redirect";
            } else if (status >= 200) {
                category = "Success";
            } else {
                category = "Unknown";
            }
            System.out.println(status + " -> " + category);
        }
    }
}
```

**How to run:** `java HttpIntermediate.java`

By checking `status >= 500` first, only genuine server errors (500 and above) match that branch; a `404` fails that first check (`404 >= 500` is `false`) and falls through to `status >= 400`, which correctly matches. Ordering from highest threshold to lowest threshold ensures each condition only "catches" the values that are actually in its intended range and haven't already been claimed by a more specific, higher-priority check earlier in the chain — this is the general pattern for any `else if` chain built from a series of `>=`/`<=` range checks.

### Level 3 — Advanced

Same classifier, now handling a genuinely ambiguous business rule (a special "deprecated but still working" status range that overlaps with the ordinary redirect range) — demonstrating that getting the *order* right requires understanding the actual business priority between overlapping cases, not just a mechanical "narrowest first" rule, and adding a self-check that verifies every code in a test range gets classified into exactly one category.

```java
public class HttpAdvanced {

    static String classify(int status) {
        // Business rule: codes 305-307 are a special "deprecated redirect" category that
        // takes priority over the general redirect category, even though 305-307 is a SUBSET
        // of the 300-399 redirect range — so it must be checked FIRST, not "narrowest numerically first."
        if (status >= 305 && status <= 307) {
            return "Deprecated Redirect";
        } else if (status >= 500) {
            return "Server Error";
        } else if (status >= 400) {
            return "Client Error";
        } else if (status >= 300) {
            return "Redirect";
        } else if (status >= 200) {
            return "Success";
        } else {
            return "Unknown";
        }
    }

    public static void main(String[] args) {
        int[] testCodes = { 200, 301, 305, 306, 307, 308, 404, 500 };
        for (int code : testCodes) {
            System.out.println(code + " -> " + classify(code));
        }

        // Self-check: every code in a realistic range should get exactly one, non-"Unknown" category
        int mismatches = 0;
        for (int code = 200; code <= 599; code++) {
            String result = classify(code);
            if (result.equals("Unknown")) {
                mismatches++;
            }
        }
        System.out.println("Codes classified as Unknown in [200,599]: " + mismatches);  // should be 0
    }
}
```

**How to run:** `java HttpAdvanced.java`

The `305-307` check is placed *first*, ahead of the general `status >= 300` redirect check, specifically because the business rule requires this narrower, overlapping subset to take priority — this shows that the correct ordering principle for `else if` chains is not simply "smaller numeric ranges before larger ones" but "more specific/higher-priority cases before more general ones that would otherwise also match," which sometimes means a numerically narrower range must be checked before a numerically broader one that overlaps it. The self-check loop iterates every status code from `200` to `599` and confirms none of them fall through to `"Unknown"` — a practical technique for gaining confidence that an `else if` chain built from range checks has no accidental gaps, especially valuable once the chain has enough branches (and enough reordering, as here) that manual inspection alone becomes less reliable.

## 6. Walkthrough

Trace `classify(306)` step by step:

**First condition.** `status >= 305 && status <= 307` evaluates `306 >= 305` (`true`) `&&` `306 <= 307` (`true`), giving `true` overall. Because `&&` requires both operands and both are `true` here, the combined condition is `true`.

**Immediate match, chain stops here.** Since this is the very first condition in the chain and it evaluated to `true`, `classify` returns `"Deprecated Redirect"` immediately. None of the remaining conditions (`>= 500`, `>= 400`, `>= 300`, `>= 200`) are ever evaluated for this call — the chain's "stop at first match" rule applies regardless of how many later conditions would *also* have matched (and in this case, `status >= 300` would also have been `true` for `306`, but it's never even checked).

```
classify(306):
  status >= 305 && status <= 307 ?   306>=305 (true) && 306<=307 (true) = TRUE
       |
       v
  return "Deprecated Redirect"   <- chain stops here

  (status >= 500?  NEVER CHECKED)
  (status >= 400?  NEVER CHECKED)
  (status >= 300?  NEVER CHECKED — even though 306 >= 300 is also true!)
  (status >= 200?  NEVER CHECKED)
```

**Contrast with `classify(308)`.** `308 >= 305 && 308 <= 307` evaluates `308 >= 305` (`true`) `&&` `308 <= 307` (`false`, since `308` is not less than or equal to `307`) — the combined condition is `false` (because `&&` requires both to be `true`). The chain proceeds to the next condition, `status >= 500` (`false` for `308`), then `status >= 400` (`false`), then `status >= 300` (`true` for `308`), which matches and returns `"Redirect"`.

**Final output.** The classifier correctly reports `305`, `306`, and `307` as `"Deprecated Redirect"` while `301` and `308` fall through to the ordinary `"Redirect"` category, and the self-check loop over the full `200`–`599` range confirms zero codes are left unclassified as `"Unknown"`, giving confidence the chain's ordering and coverage are correct.

## 7. Gotchas & takeaways

> **An `else if` chain stops at the first matching condition — every later condition is never evaluated at all, even if it would also have matched.** This means the order of conditions is not just a style preference; it directly determines which branch runs whenever more than one condition could be `true` for the same input.

> **The correct ordering rule is "more specific/higher-priority first," which is not always the same as "numerically narrower range first."** A business rule can require a subset range (like `305`-`307`) to be checked before a broader range that would otherwise contain it (`>= 300`), precisely because the subset represents a higher-priority special case.

- `else if` chains check conditions top to bottom and execute only the first branch whose condition is `true`; all subsequent conditions are skipped entirely once a match is found.
- Order conditions from most specific/highest-priority to least, especially when ranges overlap — a broad condition placed too early will "shadow" every narrower condition that comes after it.
- For range-based classification (grades, status codes, tiers), this typically means checking the highest or most restrictive threshold first, unless a specific business rule requires a different priority order for an overlapping special case.
- When a chain has many branches, a self-check that exhaustively tests a realistic range of inputs and confirms none fall through to an unexpected default is a practical way to catch ordering mistakes that are easy to miss by inspection alone.
