---
card: java
gi: 132
slug: switch-fall-through-break
title: switch fall-through & break
---

## 1. What it is

In the classic `switch` statement, once execution jumps to a matching `case` label, it does **not** automatically stop at the end of that `case`'s statements — it keeps running straight through into the next `case`'s statements, and the next, and so on, until it hits an explicit `break` statement or reaches the end of the entire `switch` block. This behavior is called **fall-through**, and it is the default — Java requires you to opt *out* of it explicitly with `break`, rather than opting into it. This is the single most common source of `switch`-related bugs: forgetting a `break` silently causes execution to continue into the next case's code.

```java
int day = 2;
switch (day) {
    case 1:
        System.out.println("Monday");
    case 2:                              // no break above — execution falls through into here too
        System.out.println("Tuesday");
    case 3:                               // and falls through into here as well!
        System.out.println("Wednesday");
        break;                             // finally stops here
    case 4:
        System.out.println("Thursday");
}
// For day == 2, this prints BOTH "Tuesday" AND "Wednesday" — likely not intended!
```

`break` immediately exits the entire `switch` statement (not just the current `case`), transferring control to whatever code follows the `switch` block.

## 2. Why & when

Fall-through is occasionally useful *deliberately*:

- Grouping multiple `case` labels to share one body, by stacking labels with no code between them (`case 1: case 2: doSomething(); break;`) — this relies on fall-through from the first label straight into the shared body, but the shared body itself still ends with a `break`.
- Implementing a genuinely cascading behavior where handling a "higher" case should also perform all the actions of "lower" cases (rare, but occasionally natural — e.g., a permission level where each tier includes all the capabilities of the tiers below it).

In the vast majority of ordinary `switch` statements, each `case` should end with `break` (or `return`, `continue`, or `throw`, any of which also exits the `switch`) to prevent unintended fall-through — omitting a `break` is far more often an accidental bug than an intentional design choice, which is why many style guides and static analysis tools flag a `case` that falls through without an explicit comment explaining that it's intentional.

## 3. Core concept

```java
public class FallThroughDemo {
    public static void main(String[] args) {
        // Accidental fall-through: a forgotten break causes unintended cascading execution
        System.out.println("--- Buggy (missing break) ---");
        int day = 2;
        switch (day) {
            case 1:
                System.out.println("Monday");
            case 2:                              // missing break above falls through into here
                System.out.println("Tuesday");
            case 3:                                // and this falls through too!
                System.out.println("Wednesday");
                break;
            case 4:
                System.out.println("Thursday");
        }

        // Correct: every case has its own break, so exactly one message prints
        System.out.println("--- Correct (every case has break) ---");
        switch (day) {
            case 1:
                System.out.println("Monday");
                break;
            case 2:
                System.out.println("Tuesday");
                break;
            case 3:
                System.out.println("Wednesday");
                break;
            case 4:
                System.out.println("Thursday");
                break;
        }

        // Deliberate fall-through: grouping labels intentionally (a good use of the behavior)
        System.out.println("--- Deliberate grouping ---");
        char grade = 'B';
        switch (grade) {
            case 'A':
            case 'B':
                System.out.println("Passing grade");   // both A and B share this body
                break;
            case 'C':
            case 'D':
                System.out.println("Needs improvement");
                break;
            default:
                System.out.println("Failing grade");
        }
    }
}
```

## 4. Diagram

<svg viewBox="0 0 700 175" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Fall-through diagram: with day equals 2 and no break after case 1 or case 2, execution enters case 2 and continues straight through case 3's statements as well, only stopping when it reaches the break statement inside case 3, printing both Tuesday and Wednesday.">
  <rect x="8" y="8" width="684" height="159" rx="8" fill="#0d1117"/>
  <text x="350" y="24" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">day = 2, missing break — execution cascades through case 2 AND case 3</text>

  <rect x="30" y="40" width="140" height="26" rx="4" fill="#1c2430" stroke="#8b949e" stroke-dasharray="3,2"/>
  <text x="100" y="57" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">case 1: (skipped)</text>

  <rect x="190" y="40" width="150" height="26" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="265" y="57" fill="#6db33f" font-size="8.5" text-anchor="middle" font-family="monospace">case 2: MATCH, print</text>

  <path d="M 340 53 L 400 53" stroke="#6db33f" stroke-width="2"/>
  <text x="370" y="45" fill="#6db33f" font-size="7.5" text-anchor="middle">no break!</text>

  <rect x="410" y="40" width="150" height="26" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="485" y="57" fill="#6db33f" font-size="8.5" text-anchor="middle" font-family="monospace">case 3: falls in, print</text>

  <path d="M 485 66 L 485 90" stroke="#6db33f" stroke-width="2"/>
  <rect x="410" y="90" width="150" height="26" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="485" y="107" fill="#79c0ff" font-size="8.5" text-anchor="middle" font-family="monospace">break; STOPS here</text>

  <text x="350" y="140" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Output: BOTH "Tuesday" (case 2) AND "Wednesday" (case 3) print — likely unintended.</text>
</svg>

Without a `break`, execution keeps flowing downward through every subsequent `case`'s statements until it finally hits one.

## 5. Runnable example

Scenario: a monthly-days calculator that determines how many days are in a given month — a genuinely idiomatic use of deliberate fall-through for grouping months with the same day count — contrasted with an accidental fall-through bug in a separate, unrelated permission-tier checker.

### Level 1 — Basic

```java
public class DaysInMonthBasic {

    static int daysInMonth(int month) {
        int days;
        switch (month) {
            case 1: case 3: case 5: case 7: case 8: case 10: case 12:
                days = 31;
                break;
            case 4: case 6: case 9: case 11:
                days = 30;
                break;
            case 2:
                days = 28;   // ignoring leap years for this basic version
                break;
            default:
                throw new IllegalArgumentException("Invalid month: " + month);
        }
        return days;
    }

    public static void main(String[] args) {
        for (int month = 1; month <= 12; month++) {
            System.out.println("Month " + month + ": " + daysInMonth(month) + " days");
        }
    }
}
```

**How to run:** `java DaysInMonthBasic.java`

`case 1: case 3: case 5: case 7: case 8: case 10: case 12:` stacks seven labels with no code between any of them — this deliberately groups every 31-day month to share the single `days = 31; break;` body, avoiding seven separate, duplicated bodies that would each just set `days = 31`. This is fall-through used exactly as intended: as a grouping mechanism, not an accident, and each group still ends with its own `break` to prevent cascading into the next group.

### Level 2 — Intermediate

A separate, unrelated permission-tier example that starts with an *accidental* fall-through bug (a forgotten `break`), then fixed — showing the two very different faces of the same underlying language feature side by side.

```java
public class PermissionIntermediate {

    static void grantAccess(int tier) {
        System.out.println("--- Buggy version for tier " + tier + " ---");
        switch (tier) {
            case 3:
                System.out.println("Admin access granted.");
                // BUG: missing break — falls through into tier 2's message too!
            case 2:
                System.out.println("Editor access granted.");
                break;
            case 1:
                System.out.println("Viewer access granted.");
                break;
            default:
                System.out.println("No access.");
        }
    }

    static void grantAccessFixed(int tier) {
        System.out.println("--- Fixed version for tier " + tier + " ---");
        switch (tier) {
            case 3:
                System.out.println("Admin access granted.");
                break;
            case 2:
                System.out.println("Editor access granted.");
                break;
            case 1:
                System.out.println("Viewer access granted.");
                break;
            default:
                System.out.println("No access.");
        }
    }

    public static void main(String[] args) {
        grantAccess(3);        // buggy: prints BOTH "Admin" and "Editor" access granted
        grantAccessFixed(3);    // fixed: prints only "Admin"
    }
}
```

**How to run:** `java PermissionIntermediate.java`

`grantAccess(3)` matches `case 3:`, prints "Admin access granted.", and then — because there is no `break` after that line — falls straight through into `case 2:`'s body, printing "Editor access granted." as well, even though tier `3` should presumably be a stricter superset, not an "and also editor" combination; this is a realistic and dangerous bug, since it could grant *additional*, unintended messages/behavior (or in a real system, unintended additional permissions) beyond what tier `3` alone should confer. `grantAccessFixed` adds the missing `break` after `case 3:`'s body, correctly stopping there and printing only the one appropriate message.

### Level 3 — Advanced

Combining both patterns in one realistic scenario: a device firmware updater that must perform a *cascading* sequence of steps for higher update levels (deliberate fall-through, where a "full" update genuinely should also perform every lower-level step) while being careful that a separate, unrelated status-reporting switch in the same class does NOT fall through, demonstrating how to reason about and clearly document which behavior is intended in each case.

```java
public class FirmwareAdvanced {

    static void performUpdate(int level) {
        System.out.println("Starting update for level " + level + ":");
        switch (level) {
            case 3:   // "full" update: intentionally cascades through every lower step too
                System.out.println("  Updating firmware core.");
                // fall through intentionally — a full update includes everything below
            case 2:   // "standard" update: also includes the driver update below
                System.out.println("  Updating device drivers.");
                // fall through intentionally — a standard update includes the config refresh too
            case 1:   // "minimal" update: just a config refresh
                System.out.println("  Refreshing configuration.");
                break;   // this break is reached by ALL three levels, ending the cascade here
            default:
                System.out.println("  Unknown update level, nothing performed.");
        }
    }

    static void reportStatus(int code) {
        // This switch is UNRELATED to the cascading logic above — every case must have its own
        // break, since each status code represents a completely distinct, non-cumulative state.
        switch (code) {
            case 0:
                System.out.println("Status: Idle");
                break;
            case 1:
                System.out.println("Status: Updating");
                break;
            case 2:
                System.out.println("Status: Complete");
                break;
            default:
                System.out.println("Status: Unknown");
        }
    }

    public static void main(String[] args) {
        performUpdate(3);   // cascades: core, drivers, AND configuration
        performUpdate(1);    // only: configuration
        reportStatus(1);      // only: "Updating" — no cascading here, by design
    }
}
```

**How to run:** `java FirmwareAdvanced.java`

`performUpdate(3)` matches `case 3:`, prints the core-update message, and (with the fall-through comment explicitly documenting the intent) continues into `case 2:`'s driver-update message, then into `case 1:`'s configuration message, finally stopping at the single shared `break;` — this genuinely models the real-world requirement that a "full" update level 3 should perform *all three* steps, not just its own. `performUpdate(1)`, by contrast, matches `case 1:` directly and only ever executes the configuration-refresh message before immediately hitting the same `break;` — it never reaches `case 2:` or `case 3:`'s code at all, because `switch` only ever jumps *into* a matching (or explicitly fallen-through) case; it cannot "restart" from an earlier case once a later one has matched. `reportStatus`, in the same class, uses a completely ordinary break-every-case structure, because its cases represent mutually exclusive, non-cumulative states where fall-through would make no logical sense.

## 6. Walkthrough

Trace `performUpdate(3)` in detail:

**Matching.** `switch (level)` compares `level` (`3`) against the `case` labels and jumps directly to `case 3:` — the intervening `case 2:` and `case 1:` labels are not "checked and skipped" the way an `if`/`else if` chain would test earlier conditions; the `switch` jumps straight to the match.

**Executing `case 3:`'s body.** `System.out.println("  Updating firmware core.")` runs. There is no `break` (only a comment noting the fall-through is intentional), so execution does not exit the `switch` — it simply continues to the next line of code in sequence, which happens to be the first statement under `case 2:`.

**Falling into `case 2:`'s body.** Execution is now physically past the `case 2:` label (having fallen into it from above, not jumped to it via matching), and runs `System.out.println("  Updating device drivers.")`. Again, no `break`, so execution continues into `case 1:`'s body next.

**Falling into `case 1:`'s body.** `System.out.println("  Refreshing configuration.")` runs.

**`break` finally stops the cascade.** The `break;` statement immediately following the configuration message is reached, and the entire `switch` statement exits — `default:` is never reached for this call, since the fall-through cascade already terminated via `break` before reaching it.

```
performUpdate(3):

switch jumps directly to case 3:  (not sequentially tested like if/else if)
  print "Updating firmware core."
  (no break -- falls through)
        |
        v
case 2: body (fallen into, not matched)
  print "Updating device drivers."
  (no break -- falls through)
        |
        v
case 1: body (fallen into, not matched)
  print "Refreshing configuration."
  break;                              <- cascade stops HERE
        |
        v
(default: never reached)
```

**Final output.** `performUpdate(3)` prints all three cascading messages; `performUpdate(1)` matches `case 1:` directly and prints only the configuration message (since it starts already past `case 3:` and `case 2:`'s labels, never executing their bodies at all); `reportStatus(1)` prints only `"Status: Updating"`, demonstrating the ordinary, non-cascading `break`-per-case pattern used correctly alongside the deliberately cascading one in the same file.

## 7. Gotchas & takeaways

> **Fall-through is the default behavior in a classic `switch` — you must explicitly `break` (or `return`/`continue`/`throw`) to prevent execution from continuing into the next `case`'s statements.** Forgetting a `break` is one of the most common and easy-to-miss bugs in Java, since the code often still compiles and even appears to "mostly work" until the specific case that falls through unexpectedly is exercised.

> **When fall-through is genuinely intentional (either for grouping labels or for a deliberate cascading effect), add an explicit comment noting that the missing `break` is on purpose.** This single habit is what separates a maintainable, deliberate use of fall-through from a landmine for the next person (including your future self) who reads or modifies the `switch` and assumes every `case` should have its own `break`.

- Fall-through means execution continues past the end of a matched `case`'s statements into the next `case`'s statements, unless stopped by `break` (or another exiting statement).
- Stacking `case` labels with no code between them (`case 1: case 2: ...`) is a deliberate, idiomatic use of fall-through for grouping several values that share one body.
- A genuinely cascading `switch` (where each level's actions include all lower levels' actions) is a legitimate, if less common, deliberate use — always document it with a comment where the `break` is conspicuously missing.
- In the overwhelming majority of ordinary switches, every `case` should end with `break` (or an equivalent exiting statement); a missing `break` is far more often an accidental bug than an intended design.
