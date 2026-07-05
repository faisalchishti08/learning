---
card: java
gi: 134
slug: while-loop
title: while loop
---

## 1. What it is

The `while` loop repeats a block of code for as long as a boolean condition remains `true`. The condition is checked **before** each iteration (including the very first), so if the condition is `false` from the start, the loop body never runs at all — this is what separates it from `do-while`, which always runs the body at least once.

```java
int count = 0;
while (count < 3) {
    System.out.println("Count: " + count);
    count++;
}
// prints: Count: 0, Count: 1, Count: 2
```

The loop keeps re-checking `count < 3` at the top of each pass; once `count` reaches `3`, the condition becomes `false` and the loop exits, resuming execution at the statement after the closing brace.

## 2. Why & when

`while` is the right tool whenever the **number of iterations is not known in advance** and instead depends on some condition that changes as the loop runs:

- Reading input or data until a sentinel value or end-of-stream is reached.
- Repeating an operation until some external state changes (a connection becomes ready, a retry succeeds).
- Implementing algorithms that naturally terminate on a condition rather than a count (e.g., halving a number until it reaches 1).

Contrast this with a `for` loop, which is preferable when you already know a fixed count or a clear init/condition/update pattern up front. `while` reads more naturally when the *condition itself* is the star of the loop, rather than a counter.

## 3. Core concept

```java
public class WhileDemo {
    public static void main(String[] args) {
        int number = 20;

        // Keep halving until we reach 1 — we don't know the iteration count in advance
        int steps = 0;
        while (number > 1) {
            number = number / 2;
            steps++;
            System.out.println("Step " + steps + ": number = " + number);
        }
        System.out.println("Reached 1 after " + steps + " steps");
    }
}
```

The condition `number > 1` is re-evaluated before every pass through the body. Because `number` changes inside the loop, the number of iterations is discovered dynamically rather than being fixed ahead of time.

## 4. Diagram

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="While loop diagram: the condition is checked first; if true the body runs and control loops back to the condition check; if false the loop exits.">
  <rect x="8" y="8" width="684" height="174" rx="8" fill="#0d1117"/>
  <text x="350" y="24" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">while (condition) { body } — condition checked BEFORE every pass</text>

  <rect x="290" y="40" width="140" height="34" rx="17" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="360" y="62" fill="#6db33f" font-size="10" text-anchor="middle" font-family="monospace">count &lt; 3 ?</text>

  <path d="M 360 74 L 360 100" stroke="#79c0ff" stroke-width="2" marker-end="url(#a)"/>
  <text x="385" y="90" fill="#79c0ff" font-size="9" font-family="sans-serif">true</text>
  <rect x="270" y="100" width="180" height="30" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="360" y="120" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">print count; count++;</text>

  <path d="M 270 115 C 180 115 180 57 288 57" stroke="#79c0ff" stroke-width="2" fill="none" marker-end="url(#a)"/>
  <text x="160" y="90" fill="#79c0ff" font-size="9" font-family="sans-serif">loop back</text>

  <path d="M 430 57 L 520 57" stroke="#f85149" stroke-width="2" marker-end="url(#b)"/>
  <text x="475" y="47" fill="#f85149" font-size="9" font-family="sans-serif">false</text>
  <rect x="520" y="42" width="140" height="30" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
  <text x="590" y="62" fill="#f85149" font-size="9" text-anchor="middle" font-family="monospace">exit loop</text>

  <text x="360" y="155" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">If the condition is false on the very first check, the body never runs at all.</text>
  <defs>
    <marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="b" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#f85149"/></marker>
  </defs>
</svg>

The condition gates every pass, including the first — a `while` loop can execute zero times.

## 5. Runnable example

Scenario: a simple countdown-based retry simulator for connecting to a service — starting with a basic counter loop, then adding a real stopping condition based on simulated success, then hardening it with a maximum-attempts safety limit so it cannot loop forever.

### Level 1 — Basic

```java
public class RetryBasic {
    public static void main(String[] args) {
        int attemptsLeft = 3;

        while (attemptsLeft > 0) {
            System.out.println("Attempt... attempts remaining after this: " + (attemptsLeft - 1));
            attemptsLeft--;
        }
        System.out.println("Done.");
    }
}
```

**How to run:** `java RetryBasic.java`

`attemptsLeft` starts at `3`. The condition `attemptsLeft > 0` is checked before each pass: it is `true` three times (`3`, `2`, `1`), and on the fourth check `attemptsLeft` is `0`, so the condition is `false` and the loop exits.

### Level 2 — Intermediate

Same retry scenario, now looping until a **simulated connection succeeds** rather than a fixed counter — the real reason `while` fits better than a `for` loop here, since we don't know in advance how many attempts it will take.

```java
public class RetryIntermediate {
    public static void main(String[] args) {
        boolean connected = false;
        int attempt = 0;
        int[] simulatedResults = { 0, 0, 1 }; // 0 = fail, 1 = succeed; attempt 3 succeeds

        while (!connected) {
            System.out.println("Attempt " + (attempt + 1) + "...");
            connected = simulatedResults[attempt] == 1;
            attempt++;
        }
        System.out.println("Connected after " + attempt + " attempt(s).");
    }
}
```

**How to run:** `java RetryIntermediate.java`

The loop condition is now `!connected` — we keep trying until the connection genuinely succeeds, however many attempts that takes. Each pass reads the next entry from `simulatedResults` to decide whether this attempt succeeds. This mirrors a real network retry: the loop's exit is driven by an outcome, not a pre-known count.

### Level 3 — Advanced

Same retry logic, now with a **maximum attempt limit** so a service that never succeeds cannot cause an infinite loop — a real production concern, since looping on `!connected` alone with no upper bound is dangerous if the condition never becomes true.

```java
public class RetryAdvanced {

    static boolean simulateConnect(int attempt) {
        // Pretend the service only comes online on the 3rd try
        return attempt == 3;
    }

    public static void main(String[] args) {
        final int maxAttempts = 5;
        boolean connected = false;
        int attempt = 0;

        while (!connected && attempt < maxAttempts) {
            attempt++;
            System.out.println("Attempt " + attempt + "...");
            connected = simulateConnect(attempt);
        }

        if (connected) {
            System.out.println("Connected after " + attempt + " attempt(s).");
        } else {
            System.out.println("Giving up after " + attempt + " attempt(s) — service unreachable.");
        }
    }
}
```

**How to run:** `java RetryAdvanced.java`

The condition is now `!connected && attempt < maxAttempts` — two conditions combined with `&&`, so the loop stops as soon as *either* we connect *or* we exhaust `maxAttempts`, whichever happens first. This guards against the classic `while` hazard: a condition that could, under some circumstance, never become false.

## 6. Walkthrough

Trace `RetryAdvanced` assuming `simulateConnect` returns `true` only when `attempt == 3` (as coded):

**Initial check.** `attempt = 0`, `connected = false`. The condition `!connected && attempt < maxAttempts` evaluates to `true && true` = `true`, so the body runs.

**Pass 1.** `attempt` becomes `1`; prints `"Attempt 1..."`; `simulateConnect(1)` returns `false` (since `1 != 3`), so `connected` stays `false`.

**Condition re-check.** `!false && 1 < 5` = `true`, loop continues.

**Pass 2.** `attempt` becomes `2`; prints `"Attempt 2..."`; `simulateConnect(2)` returns `false`.

**Pass 3.** `attempt` becomes `3`; prints `"Attempt 3..."`; `simulateConnect(3)` returns `true`, so `connected` becomes `true`.

**Final condition check.** `!true && ...` short-circuits to `false` immediately (the `&&` never even evaluates `attempt < maxAttempts`), so the loop exits.

**Result.** Since `connected` is `true`, the program prints `"Connected after 3 attempt(s)."`.

```
attempt=0 connected=false -> check: true -> run body -> attempt=1 connect? no
attempt=1 connected=false -> check: true -> run body -> attempt=2 connect? no
attempt=2 connected=false -> check: true -> run body -> attempt=3 connect? YES -> connected=true
attempt=3 connected=true  -> check: false -> EXIT LOOP
```

If `simulateConnect` never returned `true`, the same trace would instead run five times (`attempt` reaching `5`), at which point `attempt < maxAttempts` becomes `false`, the loop exits regardless of `connected`, and the program prints the "giving up" message — this is exactly the safety net the `maxAttempts` check provides.

## 7. Gotchas & takeaways

> **If nothing inside the loop body changes the variables used in the condition, the loop either never runs or never stops.** A `while (attemptsLeft > 0)` loop that forgets `attemptsLeft--` inside the body will loop forever — always double-check that every path through the body moves the condition toward becoming `false`.

> **`while` checks its condition *before* the first iteration** — if you need the body to run at least once regardless of the condition (e.g., "prompt the user, then check if they want to continue"), a `do-while` loop is the better fit, not `while`.

- Use `while` when the number of iterations depends on a condition, not a known count.
- The condition is evaluated before every pass, including the first — the body can run zero times.
- Always ensure something in the loop body can eventually make the condition `false`, or add an explicit upper bound (like `maxAttempts`) as a safety net.
- Combining conditions with `&&`/`||` (as in `!connected && attempt < maxAttempts`) is a common, idiomatic way to add a safety limit to an otherwise open-ended `while` loop.
