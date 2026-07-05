---
card: java
gi: 135
slug: do-while-loop
title: do-while loop
---

## 1. What it is

The `do-while` loop is the mirror image of `while`: it runs the loop body **first**, and only checks the boolean condition **after** each pass, at the bottom. This guarantees the body executes at least once, even if the condition is `false` from the very start — the one structural difference that justifies having both loop forms.

```java
int count = 0;
do {
    System.out.println("Count: " + count);
    count++;
} while (count < 3);
// prints: Count: 0, Count: 1, Count: 2 — same output as the while example, but the check happens after
```

Note the trailing `while (...)` must end with a semicolon — this is the one place in Java where a loop header is followed by `;`.

## 2. Why & when

`do-while` is the natural fit whenever the task is "do this thing, then decide whether to do it again" — situations where the very first execution isn't conditional on anything, because it's the thing that produces the value the condition will check:

- **Input validation / retry prompts** — you must show a prompt and read a response at least once before you can know whether to loop again.
- **Menu-driven programs** — display the menu, act on the choice, then check whether the user chose "quit."
- **Any "try once, then check the result" pattern**, such as an operation whose first attempt is unconditional and only subsequent attempts are conditional on failure.

If the loop might legitimately need to run **zero** times (the common case for most iteration), a plain `while` is more appropriate and less surprising — reach for `do-while` specifically when "at least once" is a real requirement of the logic, not just a coincidence of the data.

## 3. Core concept

```java
public class DoWhileDemo {
    public static void main(String[] args) {
        int[] responses = { -1, 5, 12, 42 }; // simulated "user input" values
        int index = 0;
        int value;

        do {
            value = responses[index];
            System.out.println("Read value: " + value);
            index++;
        } while (value < 0 && index < responses.length);

        System.out.println("Stopped after reading index " + (index - 1));
    }
}
```

The body always runs at least once (reading `responses[0]`, which is `-1`) *before* the condition `value < 0 && index < responses.length` is ever checked — this is exactly the shape of "read something, then decide whether to keep reading."

## 4. Diagram

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Do-while loop diagram: the body runs first unconditionally, then the condition is checked; if true it loops back to the body, if false it exits.">
  <rect x="8" y="8" width="684" height="174" rx="8" fill="#0d1117"/>
  <text x="350" y="24" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">do { body } while (condition) — body ALWAYS runs first, condition checked after</text>

  <rect x="270" y="42" width="180" height="30" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="360" y="62" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">run body (unconditional first time)</text>

  <path d="M 360 72 L 360 98" stroke="#e6edf3" stroke-width="2" marker-end="url(#a)"/>
  <rect x="290" y="98" width="140" height="30" rx="15" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="360" y="118" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">condition?</text>

  <path d="M 290 113 C 180 113 180 57 268 57" stroke="#79c0ff" stroke-width="2" fill="none" marker-end="url(#a)"/>
  <text x="165" y="90" fill="#79c0ff" font-size="9" font-family="sans-serif">true: loop back</text>

  <path d="M 430 113 L 520 113" stroke="#f85149" stroke-width="2" marker-end="url(#b)"/>
  <text x="475" y="103" fill="#f85149" font-size="9" font-family="sans-serif">false</text>
  <rect x="520" y="98" width="140" height="30" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
  <text x="590" y="118" fill="#f85149" font-size="9" text-anchor="middle" font-family="monospace">exit loop</text>

  <text x="360" y="155" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">Unlike while, the condition is checked AFTER the body — the first pass is never skipped.</text>
  <defs>
    <marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#e6edf3"/></marker>
    <marker id="b" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#f85149"/></marker>
  </defs>
</svg>

The body always executes once before the condition gets a say.

## 5. Runnable example

Scenario: a simple number-guessing prompt loop that keeps asking for a guess until the correct one is entered — starting basic, then adding attempt counting, then hardening it with a maximum-attempts cap so it can't loop forever on bad input.

### Level 1 — Basic

```java
public class GuessBasic {
    public static void main(String[] args) {
        int[] guesses = { 3, 7, 9 }; // simulated sequence of guesses; target is 9
        int target = 9;
        int index = 0;
        int guess;

        do {
            guess = guesses[index];
            System.out.println("Guess: " + guess);
            index++;
        } while (guess != target);

        System.out.println("Correct! The number was " + target + ".");
    }
}
```

**How to run:** `java GuessBasic.java`

The body runs unconditionally the first time, reading `guesses[0] = 3` and printing it, *before* the condition `guess != target` is ever checked. Only after that first pass does the loop decide whether to continue — it keeps going through `7`, then stops after `9` because the condition becomes `false`.

### Level 2 — Intermediate

Same guessing loop, now counting the number of attempts it actually took — a natural addition once we recognize the body always runs at least once, so "attempts" starts at a guaranteed minimum of 1.

```java
public class GuessIntermediate {
    public static void main(String[] args) {
        int[] guesses = { 3, 7, 9 };
        int target = 9;
        int index = 0;
        int attempts = 0;
        int guess;

        do {
            guess = guesses[index];
            attempts++;
            System.out.println("Attempt " + attempts + ": guessed " + guess);
            index++;
        } while (guess != target);

        System.out.println("Correct after " + attempts + " attempt(s)! The number was " + target + ".");
    }
}
```

**How to run:** `java GuessIntermediate.java`

`attempts` is incremented inside the body, which is guaranteed to run at least once — so even if `guesses[0]` happened to already equal `target`, `attempts` would correctly report `1`, not `0`. This is a subtle benefit of `do-while`'s structure: the counter naturally reflects "at least one attempt always happened."

### Level 3 — Advanced

Same guessing game, now with a **maximum attempt cap** to prevent looping past the available guesses, and explicit handling of the "never guessed correctly" outcome — a real production concern since the loop's exit condition alone (`guess != target`) provides no protection against running out of data.

```java
public class GuessAdvanced {
    public static void main(String[] args) {
        int[] guesses = { 3, 7, 5, 1 }; // target 9 is never actually guessed
        int target = 9;
        int index = 0;
        int attempts = 0;
        int guess;
        boolean found = false;

        do {
            guess = guesses[index];
            attempts++;
            System.out.println("Attempt " + attempts + ": guessed " + guess);
            found = (guess == target);
            index++;
        } while (!found && index < guesses.length);

        if (found) {
            System.out.println("Correct after " + attempts + " attempt(s)!");
        } else {
            System.out.println("Ran out of guesses after " + attempts + " attempt(s) — number was never found.");
        }
    }
}
```

**How to run:** `java GuessAdvanced.java`

The condition is now `!found && index < guesses.length` — the loop stops as soon as *either* the guess is found *or* the available guesses run out. Without the `index < guesses.length` guard, once every entry in `guesses` had been tried without a match, the next iteration would read past the end of the array and throw an `ArrayIndexOutOfBoundsException`. This is the `do-while` equivalent of the `while` loop's "always add an upper bound" lesson: the natural stopping condition (`!found`) isn't enough on its own when the data backing the loop is finite.

## 6. Walkthrough

Trace `GuessAdvanced` with `guesses = {3, 7, 5, 1}` and `target = 9` (never matched):

**First pass (unconditional).** `index = 0`, so `guess = guesses[0] = 3`; `attempts` becomes `1`; prints `"Attempt 1: guessed 3"`; `found = (3 == 9)` = `false`; `index` becomes `1`. Only now is the condition checked: `!false && 1 < 4` = `true`, so the loop continues.

**Second pass.** `guess = guesses[1] = 7`; `attempts = 2`; `found = false`; `index = 2`. Condition: `true && 2 < 4` = `true`.

**Third pass.** `guess = guesses[2] = 5`; `attempts = 3`; `found = false`; `index = 3`. Condition: `true && 3 < 4` = `true`.

**Fourth pass.** `guess = guesses[3] = 1`; `attempts = 4`; `found = false`; `index = 4`. Condition: `!false && 4 < 4` = `true && false` = `false` — the loop exits here, because `index` has now reached `guesses.length`.

**Result.** Since `found` is `false`, the program prints `"Ran out of guesses after 4 attempt(s) — number was never found."`.

```
pass 1: guess=3 found=false index=1  check(!found && index<4) -> true
pass 2: guess=7 found=false index=2  check -> true
pass 3: guess=5 found=false index=3  check -> true
pass 4: guess=1 found=false index=4  check(!found && 4<4) -> false -> EXIT
result: found=false -> "Ran out of guesses..."
```

## 7. Gotchas & takeaways

> **`do-while` always runs the body at least once — even if the condition would immediately be `false`.** If you write `do { risky(); } while (false)` expecting `risky()` to be skipped under some circumstance, it won't be; the body's first execution is entirely unconditional, no matter what the condition would otherwise evaluate to.

> **The trailing `while (condition);` needs a semicolon** — unlike every other loop or block header in Java, this is a statement, not the start of a new block, and forgetting the semicolon is a compile error.

- Use `do-while` specifically when the body must run at least once, before any condition is evaluated — not merely when it's convenient.
- Because the condition is checked after the body, any variables the condition depends on must already be updated by the time execution reaches the bottom of the loop.
- Just like `while`, a `do-while` loop driven by finite data (like an array) needs an explicit bound in its condition (e.g., `index < array.length`) to avoid running past the end of the data.
- If "zero iterations" is a valid outcome for your logic, use `while` instead — reaching for `do-while` when it isn't truly needed makes the "runs at least once" guarantee misleading to readers.
