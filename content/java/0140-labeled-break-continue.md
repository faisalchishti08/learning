---
card: java
gi: 140
slug: labeled-break-continue
title: Labeled break & continue
---

## 1. What it is

A **label** is an identifier followed by a colon placed directly before a loop (`outer:` before a `for`, `while`, etc.). A `break label;` or `continue label;` then refers to *that specific* enclosing loop instead of the innermost one — letting you exit or skip an iteration of an **outer** loop from code nested inside an **inner** loop, which a bare `break`/`continue` cannot do.

```java
outer:
for (int i = 0; i < 3; i++) {
    for (int j = 0; j < 3; j++) {
        if (i == 1 && j == 1) {
            break outer; // exits BOTH loops, not just the inner one
        }
        System.out.println(i + "," + j);
    }
}
// prints: 0,0  0,1  0,2  1,0   — then stops entirely once i=1, j=1 is reached
```

Without the label, a plain `break` at that point would only exit the inner `j` loop, and the outer `i` loop would continue on to `i = 2`.

## 2. Why & when

Labeled `break`/`continue` exist specifically for **nested loops** where the loop you need to exit or skip is not the innermost one:

- **Searching a 2D structure** (a grid, matrix, or list of lists) for a target — once found, you want to stop *all* the scanning, not just the innermost row.
- **Skipping an entire outer iteration** based on something discovered deep inside a nested loop, without extra boolean "found" flags checked at every level.
- **Avoiding flag variables** — without labels, breaking out of multiple loops usually requires a boolean flag checked in every loop's condition (`while (!found && ...)`), which is more verbose and easier to get subtly wrong than a single labeled `break`.

Labels are a deliberately rare tool — reach for them only when nested loops genuinely need to affect each other's flow; for single loops (even fairly deep logic within one loop), plain `break`/`continue` are always sufficient and preferred.

## 3. Core concept

```java
public class LabeledDemo {
    public static void main(String[] args) {
        int[][] grid = {
            { 1, 2, 3 },
            { 4, 5, 6 },
            { 7, 8, 9 }
        };
        int target = 5;
        boolean found = false;

        search:
        for (int row = 0; row < grid.length; row++) {
            for (int col = 0; col < grid[row].length; col++) {
                if (grid[row][col] == target) {
                    System.out.println("Found " + target + " at [" + row + "][" + col + "]");
                    found = true;
                    break search; // stop BOTH loops immediately — no more scanning needed
                }
            }
        }

        if (!found) {
            System.out.println(target + " not found");
        }
    }
}
```

`break search;` exits the entire labeled `for` (the outer `row` loop, and with it the inner `col` loop currently running inside it) the instant the target is found — a plain `break` here would only stop the inner `col` loop, and the outer loop would continue scanning subsequent rows for no reason.

## 4. Diagram

<svg viewBox="0 0 700 195" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Labeled break diagram: nested loops scanning a grid; a match found inside the inner loop triggers break with the outer loop's label, exiting both loops at once instead of just the inner one.">
  <rect x="8" y="8" width="684" height="179" rx="8" fill="#0d1117"/>
  <text x="350" y="24" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">search: for (row...) { for (col...) { if match: break search; } }</text>

  <rect x="60" y="45" width="580" height="120" rx="8" fill="none" stroke="#79c0ff" stroke-width="1.5" stroke-dasharray="4,3"/>
  <text x="80" y="60" fill="#79c0ff" font-size="9" font-family="monospace">outer "search:" loop (row)</text>

  <rect x="100" y="70" width="500" height="70" rx="8" fill="none" stroke="#6db33f" stroke-width="1.5" stroke-dasharray="4,3"/>
  <text x="120" y="85" fill="#6db33f" font-size="9" font-family="monospace">inner loop (col)</text>

  <rect x="140" y="95" width="140" height="30" rx="6" fill="#1c2430" stroke="#e6edf3" stroke-width="1.5"/>
  <text x="210" y="115" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="monospace">grid[row][col]==5?</text>

  <path d="M 280 110 L 360 110" stroke="#f85149" stroke-width="2" marker-end="url(#a)"/>
  <rect x="360" y="95" width="180" height="30" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="2"/>
  <text x="450" y="115" fill="#f85149" font-size="8.5" text-anchor="middle" font-family="monospace">break search;</text>

  <path d="M 450 125 L 450 175" stroke="#f85149" stroke-width="2" stroke-dasharray="3,2" marker-end="url(#b)"/>
  <text x="450" y="188" fill="#f85149" font-size="8" text-anchor="middle" font-family="sans-serif">exits BOTH loops — jumps past the outer loop's closing brace</text>

  <defs>
    <marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#f85149"/></marker>
    <marker id="b" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#f85149"/></marker>
  </defs>
</svg>

The label attaches to the outer loop; `break search;` unwinds past both loops in one step.

## 5. Runnable example

Scenario: scanning a seating chart (a grid of rows and seats) to find the first available seat matching a request — starting with a basic labeled-break search, then adding a labeled-continue to skip an entire row flagged as out of service, then hardening it to search across multiple seating sections (a third nesting level) while still exiting everything the instant a seat is found.

### Level 1 — Basic

```java
public class SeatSearchBasic {
    public static void main(String[] args) {
        String[][] chart = {
            { "X", "X", "O" },
            { "O", "X", "X" },
            { "X", "X", "X" }
        }; // "O" = open seat, "X" = taken

        rowScan:
        for (int row = 0; row < chart.length; row++) {
            for (int seat = 0; seat < chart[row].length; seat++) {
                if (chart[row][seat].equals("O")) {
                    System.out.println("First open seat: row " + row + ", seat " + seat);
                    break rowScan;
                }
            }
        }
    }
}
```

**How to run:** `java SeatSearchBasic.java`

`break rowScan;` fires as soon as the first `"O"` is found, at row 0, seat 2. Without the label, a plain `break` would only stop scanning row 0's seats, and the outer loop would then start scanning row 1 — wasted work, since row 1 has an open seat too, but we only want the *first* one found across the whole chart.

### Level 2 — Intermediate

Same seating chart, now with some rows marked entirely out of service — using a **labeled `continue`** to skip an entire out-of-service row (all of its seats) and move straight to the next row, without needing a flag variable checked in the inner loop.

```java
public class SeatSearchIntermediate {
    public static void main(String[] args) {
        String[][] chart = {
            { "X", "X", "X" },
            { "O", "X", "X" },
            { "X", "X", "X" }
        };
        boolean[] outOfService = { false, true, false }; // row 1 is out of service, despite having an "O"

        rowScan:
        for (int row = 0; row < chart.length; row++) {
            if (outOfService[row]) {
                System.out.println("Skipping entire out-of-service row " + row);
                continue rowScan; // skip this whole row, go straight to the next row
            }
            for (int seat = 0; seat < chart[row].length; seat++) {
                if (chart[row][seat].equals("O")) {
                    System.out.println("First usable open seat: row " + row + ", seat " + seat);
                    break rowScan;
                }
            }
        }
    }
}
```

**How to run:** `java SeatSearchIntermediate.java`

`continue rowScan;` here is written directly in the outer loop's own body (before the inner loop even starts), so in this particular spot it behaves the same as a plain `continue` would — but naming the label makes the intent explicit and keeps the code consistent with the `break rowScan;` used lower down. Row 1's `"O"` at seat 0 is correctly never considered, since the entire row is skipped before the inner loop that would have found it ever runs.

### Level 3 — Advanced

Same seating search, now across **multiple sections** (a third level of nesting: section → row → seat), using a labeled `break` on the outermost label to stop searching everything — every section, every row, every seat — the instant any open seat is found anywhere.

```java
public class SeatSearchAdvanced {
    public static void main(String[] args) {
        String[][][] sections = {
            { // section 0
                { "X", "X" },
                { "X", "X" }
            },
            { // section 1
                { "X", "O" },
                { "X", "X" }
            },
            { // section 2 — never reached if section 1 has an open seat
                { "O", "O" },
                { "O", "O" }
            }
        };

        boolean found = false;

        sectionScan:
        for (int section = 0; section < sections.length; section++) {
            for (int row = 0; row < sections[section].length; row++) {
                for (int seat = 0; seat < sections[section][row].length; seat++) {
                    if (sections[section][row][seat].equals("O")) {
                        System.out.println("Found open seat: section " + section + ", row " + row + ", seat " + seat);
                        found = true;
                        break sectionScan; // stop ALL THREE loops at once
                    }
                }
            }
        }

        if (!found) {
            System.out.println("No open seats anywhere.");
        }
    }
}
```

**How to run:** `java SeatSearchAdvanced.java`

`break sectionScan;` is written inside the innermost (`seat`) loop but names the **outermost** (`section`) loop's label, so it unwinds through all three nested loops in a single statement — section 2's entirely-open row is correctly never examined, since the search already stopped at section 1. This demonstrates that a label can be attached anywhere in the nesting chain and a `break`/`continue` referencing it can be issued from any loop nested inside it, regardless of how many levels deep.

## 6. Walkthrough

Trace `SeatSearchAdvanced`'s triple-nested search:

**section = 0.** `row` runs `0` then `1`; for each, `seat` runs `0` then `1`. Every entry in section 0 is `"X"`, so no `if` ever matches; all loops complete normally for this section.

**section = 1, row = 0.** `seat = 0`: `sections[1][0][0] = "X"`, no match. `seat = 1`: `sections[1][0][1] = "O"` — match! Prints `"Found open seat: section 1, row 0, seat 1"`, sets `found = true`, and executes `break sectionScan;`.

**Unwinding.** Because `sectionScan` labels the *outermost* (`section`) loop, this single `break` statement exits the innermost `seat` loop, the middle `row` loop, and the outer `section` loop all at once — execution jumps straight to the `if (!found)` check after the labeled loop, skipping `row = 1` of section 1 entirely, and all of section 2.

```
section=0: row 0,1 x seat 0,1 -> all "X", no match, loops complete normally
section=1, row=0, seat=0: "X" no match
section=1, row=0, seat=1: "O" MATCH -> break sectionScan (exits section, row, AND seat loops at once)
section=1 row=1, and all of section=2: NEVER EXAMINED
```

**Final output.** Since `found` is `true`, the program does not print the "no open seats" message — the single line printed inside the loop, `"Found open seat: section 1, row 0, seat 1"`, is the only output.

## 7. Gotchas & takeaways

> **A label by itself does nothing — it only has an effect when a `break` or `continue` explicitly names it.** Writing `outer: for (...) { ... }` with no `break outer;`/`continue outer;` anywhere inside is legal but pointless; the loop behaves exactly as it would without the label.

> **You cannot label a loop and then reference that label's `break`/`continue` from outside the loop, or from a different, unrelated loop** — the label must be lexically wrapping the code that references it; labeled `break`/`continue` are still constrained to loops (or blocks, for labeled `break`) that are actually enclosing the statement that uses the label.

- Use labeled `break`/`continue` only for nested loops, when you need to affect an outer loop from code inside an inner one — for single loops, plain `break`/`continue` are always sufficient.
- `break label;` exits the labeled loop (and everything nested inside it); `continue label;` skips to the next iteration of the labeled loop specifically.
- Labels replace the older pattern of boolean "found" flags checked in every nested loop's condition — often clearer once more than one level of nesting is involved.
- A label can be attached to any enclosing loop, however many levels out, and referenced from any statement nested inside it, no matter how deep.
